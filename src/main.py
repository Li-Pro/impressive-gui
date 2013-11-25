##### INITIALIZATION ###########################################################

def main():
    global ScreenWidth, ScreenHeight, TexWidth, TexHeight, TexSize, LogoImage
    global TexMaxS, TexMaxT, MeshStepX, MeshStepY, EdgeX, EdgeY, PixelX, PixelY
    global OverviewGridSize, OverviewCellX, OverviewCellY, HaveNPOT
    global OverviewOfsX, OverviewOfsY, OverviewBorder, OverviewImage, OverviewPageCount
    global OverviewPageMap, OverviewPageMapInv, FileName, FileList, PageCount
    global DocumentTitle, PageProps, LogoTexture, OSDFont
    global Pcurrent, Pnext, Tcurrent, Tnext, InitialPage
    global CacheFile, CacheFileName, BaseWorkingDir
    global Extensions, AllowExtensions, TextureTarget, PAR, DAR, TempFileName
    global BackgroundRendering, FileStats, RTrunning, RTrestart, StartTime
    global CursorImage, CursorVisible, InfoScriptPath
    global HalfScreen, AutoAdvance, WindowPos

    # allocate temporary file
    TempFileName = tempfile.mktemp(prefix="impressive-", suffix="_tmp")

    # some input guesswork
    BaseWorkingDir = os.getcwd()
    if not(FileName) and (len(FileList) == 1):
        FileName = FileList[0]
    if FileName and not(FileList):
        AddFile(FileName)
    if FileName:
        DocumentTitle = os.path.splitext(os.path.split(FileName)[1])[0]

    # initialize PyGame
    pygame.display.init()

    # detect screen size and compute aspect ratio
    if Fullscreen and UseAutoScreenSize:
        size = GetScreenSize()
        if size:
            ScreenWidth, ScreenHeight = size
            print >>sys.stderr, "Detected screen size: %dx%d pixels" % (ScreenWidth, ScreenHeight)
    if DAR is None:
        PAR = 1
    else:
        PAR = DAR / float(ScreenWidth) * float(ScreenHeight)

    # fill the page list
    if Shuffle:
        random.shuffle(FileList)
    PageCount = 0
    for name in FileList:
        ispdf = name.lower().endswith(".pdf")
        if ispdf:
            # PDF input -> try to pre-parse the PDF file
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
            try:
                assert 0 == subprocess.Popen([pdftkPath, name, "dump_data", "output", TempFileName + ".txt"]).wait()
                title, pages = pdftkParse(TempFileName + ".txt", PageCount)
                if title and (len(FileList) == 1):
                    DocumentTitle = title
            except KeyboardInterrupt:
                raise
            except:
                pass
        else:
            # Image File
            pages = 1
            SetPageProp(PageCount + 1, '_title', os.path.split(name)[-1])

        # validity check
        if not pages:
            print >>sys.stderr, "Warning: The input file `%s' could not be analyzed." % name
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
        print >>sys.stderr, "The presentation doesn't have any pages, quitting."
        sys.exit(1)

    # if rendering is wanted, do it NOW
    if RenderToDirectory:
        sys.exit(DoRender())

    # load and execute info script
    if not InfoScriptPath:
        InfoScriptPath = FileName + ".info"
    LoadInfoScript()

    # get the initial page number
    if not InitialPage:
        InitialPage = GetNextPage(0, 1)
    Pcurrent = InitialPage
    if (Pcurrent <= 0) or (Pcurrent > PageCount):
        print >>sys.stderr, "Attempt to start the presentation at an invalid page (%d of %d), quitting." % (InitialPage, PageCount)
        sys.exit(1)

    # initialize graphics
    pygame.display.set_caption(__title__)
    flags = OPENGL | DOUBLEBUF
    if Fullscreen:
        if FakeFullscreen:
            print >>sys.stderr, "Using \"fake-fullscreen\" mode."
            flags |= NOFRAME
            if not WindowPos:
                WindowPos = (0,0)
        else:
            flags |= FULLSCREEN
    if WindowPos:
        os.environ["SDL_VIDEO_WINDOW_POS"] = ','.join(map(str, WindowPos))
    try:
        pygame.display.set_mode((ScreenWidth, ScreenHeight), flags)
    except:
        print >>sys.stderr, "FATAL: cannot create rendering surface in the desired resolution (%dx%d)" % (ScreenWidth, ScreenHeight)
        sys.exit(1)
    pygame.key.set_repeat(500, 30)
    if Fullscreen:
        pygame.mouse.set_visible(False)
        CursorVisible = False
    glOrtho(0.0, 1.0,  1.0, 0.0,  -10.0, 10.0)
    if (Gamma <> 1.0) or (BlackLevel <> 0):
        SetGamma(force=True)

    # check if graphics are unaccelerated
    renderer = glGetString(GL_RENDERER)
    print >>sys.stderr, "OpenGL renderer:", renderer
    renderer = renderer.lower()
    if (renderer in ("mesa glx indirect", "gdi generic")) \
    or renderer.startswith("software"):
        print >>sys.stderr, "WARNING: Using an OpenGL software renderer. Impressive will work, but it will"
        print >>sys.stderr, "         very likely be too slow to be usable."

    # setup the OpenGL texture mode
    Extensions = dict([(ext.split('_', 2)[-1], None) for ext in \
                 glGetString(GL_EXTENSIONS).split()])
    if AllowExtensions and ("texture_non_power_of_two" in Extensions):
        print >>sys.stderr, "Using GL_ARB_texture_non_power_of_two."
        HaveNPOT = True
        TextureTarget = GL_TEXTURE_2D
        TexWidth  = (ScreenWidth + 3) & (-4)
        TexHeight = (ScreenHeight + 3) & (-4)
        TexMaxS = float(ScreenWidth) / TexWidth
        TexMaxT = float(ScreenHeight) / TexHeight
    elif AllowExtensions and ("texture_rectangle" in Extensions):
        print >>sys.stderr, "Using GL_ARB_texture_rectangle."
        HaveNPOT = True
        TextureTarget = 0x84F5  # GL_TEXTURE_RECTANGLE_ARB
        TexWidth  = (ScreenWidth + 3) & (-4)
        TexHeight = (ScreenHeight + 3) & (-4)
        TexMaxS = ScreenWidth
        TexMaxT = ScreenHeight
    else:
        print >>sys.stderr, "Using conventional power-of-two textures with padding."
        HaveNPOT = False
        TextureTarget = GL_TEXTURE_2D
        TexWidth  = npot(ScreenWidth)
        TexHeight = npot(ScreenHeight)
        TexMaxS = ScreenWidth  * 1.0 / TexWidth
        TexMaxT = ScreenHeight * 1.0 / TexHeight
    TexSize = TexWidth * TexHeight * 3

    # set up some variables
    MeshStepX = 1.0 / MeshResX
    MeshStepY = 1.0 / MeshResY
    PixelX = 1.0 / ScreenWidth
    PixelY = 1.0 / ScreenHeight
    EdgeX = BoxEdgeSize * 1.0 / ScreenWidth
    EdgeY = BoxEdgeSize * 1.0 / ScreenHeight

    # prepare logo image
    LogoImage = Image.open(StringIO.StringIO(LOGO))
    LogoTexture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, LogoTexture)
    glTexImage2D(GL_TEXTURE_2D, 0, 1, 256, 64, 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, LogoImage.tostring())
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    DrawLogo()
    pygame.display.flip()

    # initialize OSD font
    try:
        OSDFont = GLFont(FontTextureWidth, FontTextureHeight, FontList, FontSize, search_path=FontPath)
        DrawLogo()
        titles = []
        for key in ('title', '_title'):
            titles.extend([p[key] for p in PageProps.itervalues() if key in p])
        if titles:
            OSDFont.AddString("".join(titles))
    except ValueError:
        print >>sys.stderr, "The OSD font size is too large, the OSD will be rendered incompletely."
    except IOError:
        print >>sys.stderr, "Could not open OSD font file, disabling OSD."
    except (NameError, AttributeError, TypeError):
        print >>sys.stderr, "Your version of PIL is too old or incomplete, disabling OSD."

    # initialize mouse cursor
    if CursorImage:
        try:
            CursorImage = PrepareCustomCursor(Image.open(CursorImage))
        except:
            print >>sys.stderr, "Could not open the mouse cursor image, using standard cursor."
            CursorImage = False

    # set up page cache
    if CacheMode == PersistentCache:
        if not CacheFileName:
            CacheFileName = FileName + ".cache"
        InitPCache()
    if CacheMode == FileCache:
        CacheFile = tempfile.TemporaryFile(prefix="impressive-", suffix=".cache")

    # initialize overview metadata
    OverviewPageMap=[i for i in xrange(1, PageCount + 1) \
        if GetPageProp(i, ('overview', '_overview'), True) \
        and (i >= PageRangeStart) and (i <= PageRangeEnd)]
    OverviewPageCount = max(len(OverviewPageMap), 1)
    OverviewPageMapInv = {}
    for page in xrange(1, PageCount + 1):
        OverviewPageMapInv[page] = len(OverviewPageMap) - 1
        for i in xrange(len(OverviewPageMap)):
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
        ScreenWidth /= 2
    OverviewCellX = int(ScreenWidth  / OverviewGridSize)
    OverviewCellY = int(ScreenHeight / OverviewGridSize)
    OverviewOfsX = int((ScreenWidth  - OverviewCellX * OverviewGridSize)/2)
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
        dummy.thumbnail(ZoomToFit(dummy.size, maxsize), Image.ANTIALIAS)
    margX = int((OverviewCellX - dummy.size[0]) / 2)
    margY = int((OverviewCellY - dummy.size[1]) / 2)
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
            AutoAdvance = time_left / pages
            print >>sys.stderr, "Setting auto-advance timeout to %.1f seconds." % (0.001 * AutoAdvance)
        else:
            print >>sys.stderr, "Warning: Could not determine auto-advance timeout automatically."

    # set up background rendering
    if not EnableBackgroundRendering:
        print >>sys.stderr, "Background rendering isn't available on this platform."
        BackgroundRendering = False

    # if caching is enabled, pre-render all pages
    if CacheMode and not(BackgroundRendering):
        DrawLogo()
        DrawProgress(0.0)
        pygame.display.flip()
        for pdf in FileProps:
            if pdf.lower().endswith(".pdf"):
                ParsePDF(pdf)
        stop = False
        progress = 0.0
        for page in range(InitialPage, PageCount + 1) + range(1, InitialPage):
            event = pygame.event.poll()
            while event.type != NOEVENT:
                if event.type == KEYDOWN:
                    if (event.key == K_ESCAPE) or (event.unicode == u'q'):
                        Quit()
                    stop = True
                elif event.type == MOUSEBUTTONUP:
                    stop = True
                event = pygame.event.poll()
            if stop: break
            if (page >= PageRangeStart) and (page <= PageRangeEnd):
                PageImage(page)
            DrawLogo()
            progress += 1.0 / PageCount;
            DrawProgress(progress)
            pygame.display.flip()

    # create buffer textures
    DrawLogo()
    pygame.display.flip()
    glEnable(TextureTarget)
    Tcurrent = glGenTextures(1)
    Tnext = glGenTextures(1)
    for T in (Tcurrent, Tnext):
        glBindTexture(TextureTarget, T)
        glTexParameteri(TextureTarget, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(TextureTarget, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(TextureTarget, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameteri(TextureTarget, GL_TEXTURE_WRAP_T, GL_CLAMP)

    # prebuffer current and next page
    Pnext = 0
    RenderPage(Pcurrent, Tcurrent)
    PageEntered(update_time=False)
    PreloadNextPage(GetNextPage(Pcurrent, 1))

    # some other preparations
    PrepareTransitions()
    GenerateSpotMesh()
    if PollInterval:
        pygame.time.set_timer(USEREVENT_POLL_FILE, PollInterval * 1000)

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
    StartTime = pygame.time.get_ticks()
    pygame.time.set_timer(USEREVENT_TIMER_UPDATE, 100)
    if not(Fullscreen) and CursorImage:
        pygame.mouse.set_visible(False)
    if FadeInOut:
        LeaveFadeMode()
    else:
        DrawCurrentPage()
    UpdateCaption(Pcurrent)
    while True:
        HandleEvent(pygame.event.wait())


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
            print >>sys.stderr
            print >>sys.stderr, 79 * "="
            print >>sys.stderr, "OOPS! Impressive crashed!"
            print >>sys.stderr, "This shouldn't happen. Please report this incident to the author, including the"
            print >>sys.stderr, "full output of the program, particularly the following lines. If possible,"
            print >>sys.stderr, "please also send the input files you used."
            print >>sys.stderr
            print >>sys.stderr, "Python version:", sys.version
            print >>sys.stderr, "PyGame version:", pygame.__version__
            print >>sys.stderr, "PIL version:", Image.VERSION
            print >>sys.stderr, "PyOpenGL version:", OpenGL.__version__
            if hasattr(os, 'uname'):
                uname = os.uname()
                print >>sys.stderr, "Operating system: %s %s (%s)" % (uname[0], uname[2], uname[4])
            else:
                print >>sys.stderr, "Python platform:", sys.platform
            if os.path.isfile("/usr/bin/lsb_release"):
                lsb_release = subprocess.Popen(["/usr/bin/lsb_release", "-sd"], stdout=subprocess.PIPE)
                print >>sys.stderr, "Linux distribution:", lsb_release.stdout.read().strip()
                lsb_release.wait()
            print >>sys.stderr, "Command line:", ' '.join(('"%s"'%arg if (' ' in arg) else arg) for arg in sys.argv)
            raise
    finally:
        StopMPlayer()
        # ensure that background rendering is halted
        Lrender.acquire()
        Lcache.acquire()
        # remove all temp files
        if 'CacheFile' in globals():
            del CacheFile
        for tmp in glob.glob(TempFileName + "*"):
            try:
                os.remove(tmp)
            except OSError:
                pass
        pygame.quit()

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
