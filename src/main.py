##### INITIALIZATION ###########################################################

LoadDefaultBindings()

def main():
    global gl, ScreenWidth, ScreenHeight, TexWidth, TexHeight, TexSize
    global TexMaxS, TexMaxT, PixelX, PixelY, LogoImage
    global OverviewGridSize, OverviewCellX, OverviewCellY
    global OverviewOfsX, OverviewOfsY, OverviewBorder, OverviewImage, OverviewPageCount
    global OverviewPageMap, OverviewPageMapInv, FileName, FileList, PageCount
    global DocumentTitle, PageProps, LogoTexture, OSDFont
    global Pcurrent, Pnext, Tcurrent, Tnext, InitialPage
    global CacheFile, CacheFileName, BaseWorkingDir, RenderToDirectory
    global PAR, DAR, TempFileName, Bare, MaxZoomFactor
    global BackgroundRendering, FileStats, RTrunning, RTrestart, StartTime
    global CursorImage, CursorVisible, InfoScriptPath
    global HalfScreen, AutoAdvanceTime, AutoAdvanceEnabled, WindowPos
    global BoxFadeDarknessBase, BoxZoomDarknessBase, SpotRadiusBase
    global BoxIndexBuffer, UseBlurShader, MouseHideDelay

    # allocate temporary file
    TempFileName = None
    try:
        TempFileName = tempfile.mktemp(prefix="impressive-", suffix="_tmp")
    except EnvironmentError:
        if not Bare:
            print("Could not allocate temporary file, reverting to --bare mode.", file=sys.stderr)
        Bare = True

    # some input guesswork
    BaseWorkingDir = os.getcwd()
    if not(FileName) and (len(FileList) == 1):
        FileName = FileList[0]
    if FileName and not(FileList):
        AddFile(FileName)
    if FileName:
        DocumentTitle = os.path.splitext(os.path.split(FileName)[1])[0]

    # early graphics initialization
    Platform.Init()

    # detect screen size and compute aspect ratio
    if Fullscreen and (UseAutoScreenSize or not(Platform.allow_custom_fullscreen_res)):
        size = Platform.GetScreenSize()
        if size:
            ScreenWidth, ScreenHeight = size
            print("Detected screen size: %dx%d pixels" % (ScreenWidth, ScreenHeight), file=sys.stderr)
    if DAR is None:
        PAR = 1.0
        DAR = float(ScreenWidth) / float(ScreenHeight)
    else:
        PAR = DAR / float(ScreenWidth) * float(ScreenHeight)

    # override some irrelevant settings in event test mode
    if EventTestMode:
        FileList = ["XXX.EventTestDummy.XXX"]
        InfoScriptPath = None
        RenderToDirectory = False
        InitialPage = None
        HalfScreen = False

    # fill the page list
    if Shuffle:
        random.shuffle(FileList)
    PageCount = 0
    for name in FileList:
        ispdf = name.lower().endswith(".pdf")
        if ispdf:
            # PDF input -> initialize renderers and if none available, reject
            if not InitPDFRenderer():
                print("Ignoring unrenderable input file '%s'." % name, file=sys.stderr)
                continue

            # try to pre-parse the PDF file
            pages = 0
            out = [(ScreenWidth + Overscan, ScreenHeight + Overscan),
                   (ScreenWidth + Overscan, ScreenHeight + Overscan)]
            res = [(72.0, 72.0), (72.0, 72.0)]

            # phase 1: internal PDF parser
            try:
                pages, pdf_width, pdf_height = analyze_pdf(name)
                out = [ZoomToFit((pdf_width, pdf_height * PAR)),
                       ZoomToFit((pdf_height, pdf_width * PAR))]
                res = [(out[0][0] * 72.0 / pdf_width, out[0][1] * 72.0 / pdf_height),
                       (out[1][1] * 72.0 / pdf_width, out[1][0] * 72.0 / pdf_height)]
            except KeyboardInterrupt:
                raise
            except:
                pass

            # phase 2: use pdftk
            if pdftkPath and TempFileName:
                try:
                    assert 0 == Popen([pdftkPath, name, "dump_data_utf8", "output", TempFileName + ".txt"]).wait()
                    title, pages = pdftkParse(TempFileName + ".txt", PageCount)
                    if title and (len(FileList) == 1):
                        DocumentTitle = title
                except KeyboardInterrupt:
                    raise
                except:
                    print("pdftkParse() FAILED")
                    pass

            # phase 3: use mutool (if pdftk wasn't successful)
            if not(pages) and mutoolPath:
                try:
                    proc = Popen([mutoolPath, "info", name], stdout=subprocess.PIPE)
                    title, pages = mutoolParse(proc.stdout)
                    assert 0 == proc.wait()
                    if title and (len(FileList) == 1):
                        DocumentTitle = title
                except KeyboardInterrupt:
                    raise
                except:
                    pass
        else:
            # image or video file
            pages = 1
            if IsVideoFile(name):
                SetPageProp(PageCount + 1, '_video', True)
            SetPageProp(PageCount + 1, '_title', os.path.split(name)[-1])

        # validity check
        if not pages:
            print("WARNING: The input file `%s' could not be analyzed." % name, file=sys.stderr)
            continue

        # add pages and files into PageProps and FileProps
        pagerange = list(range(PageCount + 1, PageCount + pages + 1))
        for page in pagerange:
            SetPageProp(page, '_file', name)
            if ispdf: SetPageProp(page, '_page', page - PageCount)
            title = GetFileProp(name, 'title')
            if title: SetPageProp(page, '_title', title)
        SetFileProp(name, 'pages', GetFileProp(name, 'pages', []) + pagerange)
        SetFileProp(name, 'offsets', GetFileProp(name, 'offsets', []) + [PageCount])
        if not GetFileProp(name, 'stat'): SetFileProp(name, 'stat', my_stat(name))
        if ispdf:
            SetFileProp(name, 'out', out)
            SetFileProp(name, 'res', res)
        PageCount += pages

    # no pages? strange ...
    if not PageCount:
        print("The presentation doesn't have any pages, quitting.", file=sys.stderr)
        sys.exit(1)

    # if rendering is wanted, do it NOW
    if RenderToDirectory:
        sys.exit(DoRender())

    # load and execute info script
    if not InfoScriptPath:
        InfoScriptPath = FileName + ".info"
    LoadInfoScript()

    # initialize some derived variables
    BoxFadeDarknessBase = BoxFadeDarkness
    BoxZoomDarknessBase = BoxZoomDarkness
    SpotRadiusBase = SpotRadius
    if MouseHideDelay is None:
        MouseHideDelay = DefaultMouseHideDelay if Fullscreen else 0

    # get the initial page number
    if not InitialPage:
        InitialPage = GetNextPage(0, 1)
    Pcurrent = InitialPage
    if (Pcurrent <= 0) or (Pcurrent > PageCount):
        print("Attempt to start the presentation at an invalid page (%d of %d), quitting." % (InitialPage, PageCount), file=sys.stderr)
        sys.exit(1)

    # initialize graphics
    try:
        Platform.StartDisplay()
    except Exception as e:
        print("FATAL: failed to create rendering surface in the desired resolution (%dx%d)" % (ScreenWidth, ScreenHeight), file=sys.stderr)
        print("       detailed error message:", e, file=sys.stderr)
        sys.exit(1)
    if Fullscreen:
        Platform.SetMouseVisible(False)
        CursorVisible = False
    if (Gamma != 1.0) or (BlackLevel != 0):
        SetGamma(force=True)

    # initialize OpenGL
    try:
        gl = Platform.LoadOpenGL()
        print("OpenGL renderer:", GLRenderer, file=sys.stderr)

        # check if graphics are unaccelerated
        renderer = GLRenderer.lower().replace(' ', '').replace('(r)', '')
        if not(renderer) \
        or (renderer in ("mesaglxindirect", "gdigeneric")) \
        or renderer.startswith("software") \
        or ("llvmpipe" in renderer):
            print("WARNING: Using an OpenGL software renderer. Impressive will work, but it will", file=sys.stderr)
            print("         very likely be too slow to be usable.", file=sys.stderr)

        # check for old hardware that can't deal with the blur shader
        for substr in ("i915", "intel915", "intel945", "intelq3", "intelg3", "inteligd", "gma900", "gma950", "gma3000", "gma3100", "gma3150"):
            if substr in renderer:
                UseBlurShader = False

        # check the OpenGL version (2.0 needed to ensure NPOT texture support)
        extensions = set((gl.GetString(gl.EXTENSIONS) or "").split())
        if (GLVersion < "2") and (not("GL_ARB_shader_objects" in extensions) or not("GL_ARB_texture_non_power_of_two" in extensions)):
            raise ImportError("OpenGL version %r is below 2.0 and the necessary extensions are unavailable" % GLVersion)
    except ImportError as e:
        if GLVendor: print("OpenGL vendor:", GLVendor, file=sys.stderr)
        if GLRenderer: print("OpenGL renderer:", GLRenderer, file=sys.stderr)
        if GLVersion: print("OpenGL version:", GLVersion, file=sys.stderr)
        print("FATAL:", e, file=sys.stderr)
        print("This likely means that your graphics driver or hardware is too old.", file=sys.stderr)
        sys.exit(1)

    # some further OpenGL configuration
    if Verbose:
        GLShader.LOG_DEFAULT = GLShader.LOG_IF_NOT_EMPTY
    for shader in RequiredShaders:
        shader.get_instance()
    if UseBlurShader:
        try:
            BlurShader.get_instance()
        except GLShaderCompileError:
            UseBlurShader = False
    if Verbose:
        if UseBlurShader:
            print("Using blur-and-desaturate shader for highlight box and spotlight mode.", file=sys.stderr)
        else:
            print("Using legacy multi-pass blur for highlight box and spotlight mode.", file=sys.stderr)
    gl.BlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
    BoxIndexBuffer = HighlightIndexBuffer(4)

    # set up the OpenGL texture size (identical to the screen size because we
    # require non-power-of-two texture support by now)
    gl.PixelStorei(gl.UNPACK_ALIGNMENT, 1)
    TexWidth  = ScreenWidth
    TexHeight = ScreenHeight
    TexMaxS = 1.0
    TexMaxT = 1.0
    TexSize = TexWidth * TexHeight * 3

    # determine maximum texture size
    maxsize = c_int(0)
    gl.GetIntegerv(gl.MAX_TEXTURE_SIZE, ctypes.byref(maxsize))
    maxsize = float(maxsize.value)
    if (maxsize > ScreenWidth) and (maxsize <= 65536):
        MaxZoomFactor = min(MaxZoomFactor, maxsize / ScreenWidth, maxsize / ScreenHeight)
    if Verbose:
        print("Maximum texture size is %.0f pixels, using maximum zoom level of %.1f." % (maxsize, MaxZoomFactor), file=sys.stderr)

    # set up some variables
    PixelX = 1.0 / ScreenWidth
    PixelY = 1.0 / ScreenHeight
    ScreenAspect = float(ScreenWidth) / float(ScreenHeight)

    # prepare logo image
    LogoImage = Image.open(io.BytesIO(codecs.decode(LOGO, 'base64')))
    LogoTexture = gl.make_texture(gl.TEXTURE_2D, filter=gl.NEAREST, img=LogoImage)
    DrawLogo()
    Platform.SwapBuffers()

    # initialize OSD font
    try:
        OSDFont = GLFont(FontTextureWidth, FontTextureHeight, FontList, FontSize, search_path=FontPath)
        DrawLogo()
        titles = []
        for key in ('title', '_title'):
            titles.extend([p[key] for p in PageProps.values() if key in p])
        if titles:
            OSDFont.AddString("".join(titles))
    except ValueError:
        print("The OSD font size is too large, the OSD will be rendered incompletely.", file=sys.stderr)
    except IOError:
        print("Could not open OSD font file, disabling OSD.", file=sys.stderr)
    except (NameError, AttributeError, TypeError):
        print("Your version of PIL is too old or incomplete, disabling OSD.", file=sys.stderr)

    # handle event test mode
    if EventTestMode:
        DoEventTestMode()

    # initialize mouse cursor
    if (MouseHideDelay != 1) and (CursorImage or not(Platform.has_hardware_cursor)):
        img = None
        if CursorImage and not(CursorImage.lower() in ("-", "default")):
            try:
                img = Image.open(CursorImage).convert('RGBA')
                img.load()
            except:
                print("Could not open the mouse cursor image, using standard cursor.", file=sys.stderr)
                img = None
        CursorImage = PrepareCustomCursor(img)
    else:
        CursorImage = None

    # set up page cache
    if CacheMode == PersistentCache:
        if not CacheFileName:
            CacheFileName = FileName + ".cache"
        InitPCache()
    if CacheMode == FileCache:
        CacheFile = tempfile.TemporaryFile(prefix="impressive-", suffix=".cache")

    # overview preparations
    if EnableOverview:
        # initialize overview metadata
        OverviewPageMap=[i for i in range(1, PageCount + 1) \
            if GetPageProp(i, ('overview', '_overview'), True) \
            and (i >= PageRangeStart) and (i <= PageRangeEnd)]
        OverviewPageCount = max(len(OverviewPageMap), 1)
        OverviewPageMapInv = {}
        for page in range(1, PageCount + 1):
            OverviewPageMapInv[page] = len(OverviewPageMap) - 1
            for i in range(len(OverviewPageMap)):
                if OverviewPageMap[i] >= page:
                    OverviewPageMapInv[page] = i
                    break

        # initialize overview page geometry
        OverviewGridSize = 1
        while OverviewPageCount > OverviewGridSize * OverviewGridSize:
            OverviewGridSize += 1
        if HalfScreen:
            # in half-screen mode, temporarily override ScreenWidth
            saved_screen_width = ScreenWidth
            ScreenWidth //= 2
        OverviewCellX = ScreenWidth  // OverviewGridSize
        OverviewCellY = ScreenHeight // OverviewGridSize
        OverviewOfsX = (ScreenWidth  - OverviewCellX * OverviewGridSize) // 2
        OverviewOfsY = int((ScreenHeight - OverviewCellY * \
                       int((OverviewPageCount + OverviewGridSize - 1) / OverviewGridSize)) / 2)
        while OverviewBorder and (min(OverviewCellX - 2 * OverviewBorder, OverviewCellY - 2 * OverviewBorder) < 16):
            OverviewBorder -= 1
        OverviewImage = Image.new('RGB', (TexWidth, TexHeight))
        if HalfScreen:
            OverviewOfsX += ScreenWidth
            ScreenWidth = saved_screen_width

        # fill overlay "dummy" images
        dummy = LogoImage.copy()
        border = max(OverviewLogoBorder, 2 * OverviewBorder)
        maxsize = (OverviewCellX - border, OverviewCellY - border)
        if (dummy.size[0] > maxsize[0]) or (dummy.size[1] > maxsize[1]):
            size = ZoomToFit(dummy.size, maxsize, force_int=True)
            if min(size) > 0:
                dummy.thumbnail(size, Image.ANTIALIAS)
            else:
                dummy = None
        if dummy:
            margX = (OverviewCellX - dummy.size[0]) // 2
            margY = (OverviewCellY - dummy.size[1]) // 2
            dummy = dummy.convert(mode='RGB')
            for page in range(OverviewPageCount):
                pos = OverviewPos(page)
                OverviewImage.paste(dummy, (pos[0] + margX, pos[1] + margY))
            del dummy

    # compute auto-advance timeout, if applicable
    if EstimatedDuration and AutoAutoAdvance:
        time_left = EstimatedDuration * 1000
        pages = 0
        p = InitialPage
        while p:
            override = GetPageProp(p, 'timeout')
            if override:
                time_left -= override
            else:
                pages += 1
            pnext = GetNextPage(p, 1)
            if pnext:
                time_left -= GetPageProp(p, 'transtime', TransitionDuration)
            p = pnext
        if pages and (time_left >= pages):
            AutoAdvanceTime = time_left // pages
            AutoAdvanceEnabled = True
            print("Setting auto-advance timeout to %.1f seconds." % (0.001 * AutoAdvanceTime), file=sys.stderr)
        else:
            print("Warning: Could not determine auto-advance timeout automatically.", file=sys.stderr)

    # set up background rendering
    if not HaveThreads:
        print("Note: Background rendering isn't available on this platform.", file=sys.stderr)
        BackgroundRendering = False

    # if caching is enabled, pre-render all pages
    if CacheMode and not(BackgroundRendering):
        DrawLogo()
        DrawProgress(0.0)
        Platform.SwapBuffers()
        for pdf in FileProps:
            if pdf.lower().endswith(".pdf"):
                ParsePDF(pdf)
        stop = False
        progress = 0.0
        def prerender_action_handler(action):
            if action in ("$quit", "*quit"):
                Quit()
        for page in list(range(InitialPage, PageCount + 1)) + list(range(1, InitialPage)):
            while True:
                ev = Platform.GetEvent(poll=True)
                if not ev: break
                ProcessEvent(ev, prerender_action_handler)
                if ev.startswith('*'):
                    stop = True
            if stop: break
            if (page >= PageRangeStart) and (page <= PageRangeEnd):
                PageImage(page)
            DrawLogo()
            progress += 1.0 / PageCount
            DrawProgress(progress)
            Platform.SwapBuffers()

    # create buffer textures
    DrawLogo()
    Platform.SwapBuffers()
    Tcurrent, Tnext = [gl.make_texture(gl.TEXTURE_2D, gl.CLAMP_TO_EDGE, gl.LINEAR) for dummy in (1,2)]

    if not _hook.run_editor():
        return

    # prebuffer current and next page
    Pnext = 0
    RenderPage(Pcurrent, Tcurrent)
    if not FadeInOut:
        DrawCurrentPage()
    PageEntered(update_time=False)
    PreloadNextPage(GetNextPage(Pcurrent, 1))

    # some other preparations
    PrepareTransitions()
    GenerateSpotMesh()
    if PollInterval:
        Platform.ScheduleEvent("$poll-file", PollInterval * 1000, periodic=True)

    # start the background rendering thread
    if CacheMode and BackgroundRendering:
        RTrunning = True
        thread.start_new_thread(RenderThread, (Pcurrent, Pnext))

    # parse PDF file if caching is disabled
    if not CacheMode:
        for pdf in FileProps:
            if pdf.lower().endswith(".pdf"):
                SafeCall(ParsePDF, [pdf])

    # start output and enter main loop
    StartTime = Platform.GetTicks()
    if TimeTracking or TimeDisplay:
        EnableTimeTracking(True)
    Platform.ScheduleEvent("$timer-update", 100, periodic=True)
    if (MouseHideDelay == 1) or CursorImage:
        Platform.SetMouseVisible(False)
    if FadeInOut:
        LeaveFadeMode()
    else:
        DrawCurrentPage()
    UpdateCaption(Pcurrent)
    EventHandlerLoop()  # never returns


# event test mode implementation
def DoEventTestMode():
    last_event = "(None)"
    need_redraw = True
    cx = ScreenWidth // 2
    y1 = ScreenHeight // 5
    y2 = (ScreenHeight * 4) // 5
    if OSDFont:
        dy = OSDFont.GetLineHeight()
    Platform.ScheduleEvent('$dummy', 1000)  # required to ensure that time measurement works :(
    print("Entering Event Test Mode.", file=sys.stderr)
    print(" timestamp | delta-time | event")
    t0 = Platform.GetTicks()
    while True:
        if need_redraw:
            DrawLogo()
            if OSDFont:
                gl.Enable(gl.BLEND)
                OSDFont.BeginDraw()
                OSDFont.Draw((cx, y1 - dy), "Event Test Mode", align=Center, beveled=False, bold=True)
                OSDFont.Draw((cx, y1), "press Alt+F4 to quit", align=Center, beveled=False)
                OSDFont.Draw((cx, y2 - dy), "Last Event:", align=Center, beveled=False, bold=True)
                OSDFont.Draw((cx, y2), last_event, align=Center, beveled=False)
                OSDFont.EndDraw()
                gl.Disable(gl.BLEND)
            Platform.SwapBuffers()
            need_redraw = False
        ev = Platform.GetEvent()
        if ev == '$expose':
            need_redraw = True
        elif ev == '$quit':
            Quit()
        elif ev and ev.startswith('*'):
            now = Platform.GetTicks()
            print("%7d ms | %7d ms | %s" % (int(now), int(now - t0), ev[1:]))
            t0 = now
            last_event = ev[1:]
            need_redraw = True


# wrapper around main() that ensures proper uninitialization
def run_main():
    global CacheFile
    try:
        try:
            main()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            pass
        except:
            print(file=sys.stderr)
            print(79 * "=", file=sys.stderr)
            print("OOPS! Impressive crashed!", file=sys.stderr)
            print("This shouldn't happen. Please report this incident to the author, including the", file=sys.stderr)
            print("full output of the program, particularly the following lines. If possible,", file=sys.stderr)
            print("please also send the input files you used.", file=sys.stderr)
            print(file=sys.stderr)
            print("Impressive version:", __version__, file=sys.stderr)
            print("Python version:", sys.version.replace('\r', '').replace('\n', ' ').replace('  ', ' '), file=sys.stderr)
            print("Impressive platform:", Platform.name)
            print("PyGame version:", pygame.version.ver, file=sys.stderr)
            print("SDL version:", '.'.join(map(str, pygame.get_sdl_version())), file=sys.stderr)
            if hasattr(Image, "__version__"):  # Pillow >= 5.2
                print("PIL version: Pillow", Image.__version__, file=sys.stderr)
            elif hasattr(Image, "PILLOW_VERSION"):  # Pillow < 7.0
                print("PIL version: Pillow", Image.PILLOW_VERSION, file=sys.stderr)
            elif hasattr(Image, "VERSION"):  # classic PIL or Pillow 1.x
                print("PIL version: classic", Image.VERSION, file=sys.stderr)
            else:
                print("PIL version: unknown", file=sys.stderr)            
            if PDFRenderer:
                print("PDF renderer:", PDFRenderer.name, file=sys.stderr)
            else:
                print("PDF renderer: None", file=sys.stderr)
            if GLVendor: print("OpenGL vendor:", GLVendor, file=sys.stderr)
            if GLRenderer: print("OpenGL renderer:", GLRenderer, file=sys.stderr)
            if GLVersion: print("OpenGL version:", GLVersion, file=sys.stderr)
            if hasattr(os, 'uname'):
                uname = os.uname()
                print("Operating system: %s %s (%s)" % (uname[0], uname[2], uname[4]), file=sys.stderr)
            else:
                print("Python platform:", sys.platform, file=sys.stderr)
            if os.path.isfile("/usr/bin/lsb_release"):
                lsb_release = Popen(["/usr/bin/lsb_release", "-sd"], stdout=subprocess.PIPE)
                print("Linux distribution:", lsb_release.stdout.read().decode().strip(), file=sys.stderr)
                lsb_release.wait()
            if basestring != str:
                cmdline = b' '.join((b'"%s"'%arg if (b' ' in arg) else arg) for arg in sys.argv)
            else:
                cmdline = ' '.join(('"%s"'%arg if (' ' in arg) else arg) for arg in sys.argv)
            print("Command line:", cmdline, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    finally:
        StopMPlayer()
        # ensure that background rendering is halted
        Lrender.acquire()
        Lcache.acquire()
        # remove all temp files
        if 'CacheFile' in globals():
            del CacheFile
        if TempFileName:
            for tmp in glob.glob(TempFileName + "*"):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        Platform.Quit()

    # release all locks
    try:
        if Lrender.locked():
            Lrender.release()
    except:
        pass
    try:
        if Lcache.locked():
            Lcache.release()
    except:
        pass
    try:
        if Loverview.locked():
            Loverview.release()
    except:
        pass
