##### PAGE RENDERING ###########################################################

class RenderError(RuntimeError):
    pass
class RendererUnavailable(RenderError):
    pass

class PDFRendererBase(object):
    name = None
    binaries = []
    test_run_args = []
    supports_anamorphic = False
    required_options = []
    needs_tempfile = True

    @classmethod
    def supports(self, binary):
        if not binary:
            return True
        binary = os.path.basename(binary).lower()
        if binary.endswith(".exe"):
            binary = binary[:-4]
        return (binary in self.binaries)

    def __init__(self, binary=None):
        if self.needs_tempfile and not(TempFileName):
            raise RendererUnavailable("temporary file creation required, but not available")

        # search for a working binary and run it to get a list of its options
        self.command = None
        for program_spec in map(str.split, ([binary] if binary else self.binaries)):
            test_binary = FindBinary(program_spec[0])
            try:
                p = subprocess.Popen([test_binary] + program_spec[1:] + self.test_run_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                data = p.stdout.read()
                p.wait()
            except OSError:
                continue
            self.command = [test_binary] + program_spec[1:]
            break
        if not self.command:
            raise RendererUnavailable("program not found")

        # parse the output into an option list
        data = [line.strip().replace('\t', ' ') for line in data.split('\n')]
        self.options = set([line.split(' ', 1)[0].split('=', 1)[0].strip('-,') for line in data if line.startswith('-')])
        if not(set(self.required_options) <= self.options):
            raise RendererUnavailable("%s does not support all required options" % os.path.basename(self.command[0]))

    def render(self, filename, page, res, antialias=True):
        raise RenderError()

    def execute(self, args, wait=True, redirect=False):
        args = self.command + args
        if get_thread_id() == RTrunning:
            args = Nice + args
        try:
            if redirect:
                process = subprocess.Popen(args, stdout=subprocess.PIPE)
            else:
                process = subprocess.Popen(args)
            if not wait:
                return process
            if process.wait() != 0:
                raise RenderError("rendering failed")
        except OSError, e:
            raise RenderError("could not start renderer - %s" % e)

    def load(self, imgfile, autoremove=False):
        try:
            img = Image.open(imgfile)
            img.load()
        except (KeyboardInterrupt, SystemExit):
            raise
        except IOError, e:
            raise RenderError("could not read image file - %s" % e)
        if autoremove:
            self.remove(imgfile)
        return img

    def remove(self, tmpfile):
        try:
            os.unlink(tmpfile)
        except OSError:
            pass


class MuPDFRenderer(PDFRendererBase):
    name = "MuPDF 1.4 or newer"
    binaries = ["mudraw", "mutool draw"]
    test_run_args = []
    required_options = ["F", "c", "o", "r"]
    needs_tempfile = (os.name == 'nt')

    def render(self, filename, page, res, antialias=True):
        # direct stdout pipe from mutool on Unix; not possible on Win32
        # because mutool does LF->CRLF mangling on the image data
        pipe = (os.name != 'nt')
        imgfile = "-" if pipe else (TempFileName + ".ppm")
        if ("A" in self.options) and not(antialias):
            aa_opts = ["-A", "0"]
        else:
            aa_opts = []
        proc = self.execute(
            ["-F", "pnm", "-c", "rgb", "-o", imgfile, "-r", str(res[0])] \
            + aa_opts + [filename, str(page)],
            wait=not(pipe), redirect=pipe)
        if pipe:
            try:
                out, err = proc.communicate()
            except EnvironmentError, e:
                raise RenderError("could not run renderer - %s" % e)
            if not out:
                raise RenderError("renderer returned empty image")
            return self.load(cStringIO.StringIO(out))
        else:
            return self.load(imgfile, autoremove=True)
AvailableRenderers.append(MuPDFRenderer)


class MuPDFLegacyRenderer(PDFRendererBase):
    name = "MuPDF (legacy)"
    binaries = ["mudraw", "pdfdraw"]
    test_run_args = []
    required_options = ["o", "r"]

    # helper object for communication with the reader thread
    class ThreadComm(object):
        def __init__(self, imgfile):
            self.imgfile = imgfile
            self.buffer = None
            self.error = None
            self.cancel = False

        def getbuffer(self):
            if self.buffer:
                return self.buffer
            # the reader thread might still be busy reading the last
            # chunks of the data and converting them into a StringIO;
            # let's give it some time
            maxwait = time.time() + (0.1 if self.error else 0.5)
            while not(self.buffer) and (time.time() < maxwait):
                time.sleep(0.01)
            return self.buffer

    @staticmethod
    def ReaderThread(comm):
        try:
            f = open(comm.imgfile, 'rb')
            comm.buffer = cStringIO.StringIO(f.read())
            f.close()
        except IOError, e:
            comm.error = "could not open FIFO for reading - %s" % e

    def render(self, filename, page, res, antialias=True):
        imgfile = TempFileName + ".ppm"
        fifo = False
        if HaveThreads:
            self.remove(imgfile)
            try:
                os.mkfifo(imgfile)
                fifo = True
                comm = self.ThreadComm(imgfile)
                thread.start_new_thread(self.ReaderThread, (comm, ))
            except (OSError, IOError, AttributeError):
                pass
        if ("b" in self.options) and not(antialias):
            aa_opts = ["-b", "0"]
        else:
            aa_opts = []
        try:
            self.execute([
                "-o", imgfile,
                "-r", str(res[0]),
                ] + aa_opts + [
                filename,
                str(page)
            ])
            if fifo:
                if comm.error:
                    raise RenderError(comm.error)
                if not comm.getbuffer():
                    raise RenderError("could not read from FIFO")
                return self.load(comm.buffer, autoremove=False)
            else:
                return self.load(imgfile)
        finally:
            if fifo:
                comm.error = True
                if not comm.getbuffer():
                    # if rendering failed and the client process didn't write
                    # to the FIFO at all, the reader thread would block in
                    # read() forever; so let's open+close the FIFO to
                    # generate an EOF and thus wake the thead up
                    try:
                        f = open(imgfile, "w")
                        f.close()
                    except IOError:
                        pass
            self.remove(imgfile)
AvailableRenderers.append(MuPDFLegacyRenderer)


class XpdfRenderer(PDFRendererBase):
    name = "Xpdf/Poppler"
    binaries = ["pdftoppm"]
    test_run_args = ["-h"]
    required_options = ["q", "f", "l", "r"]

    def __init__(self, binary=None):
        PDFRendererBase.__init__(self, binary)
        self.supports_anamorphic = ('rx' in self.options) and ('ry' in self.options)

    def render(self, filename, page, res, antialias=True):
        if self.supports_anamorphic:
            args = ["-rx", str(res[0]), "-ry", str(res[1])]
        else:
            args = ["-r", str(res[0])]
        if not antialias:
            for arg in ("aa", "aaVector"):
                if arg in self.options:
                    args += ['-'+arg, 'no']
        self.execute([
            "-q",
            "-f", str(page),
            "-l", str(page)
            ] + args + [
            filename,
            TempFileName
        ])
        digits = GetFileProp(filename, 'digits', 6)
        try_digits = range(6, 0, -1)
        try_digits.sort(key=lambda n: abs(n - digits))
        try_digits = [(n, TempFileName + ("-%%0%dd.ppm" % n) % page) for n in try_digits]
        for digits, imgfile in try_digits:
            if not os.path.exists(imgfile):
                continue
            SetFileProp(filename, 'digits', digits)
            return self.load(imgfile, autoremove=True)
        raise RenderError("could not find generated image file")
AvailableRenderers.append(XpdfRenderer)

class GhostScriptRenderer(PDFRendererBase):
    name = "GhostScript"
    binaries = ["gs", "gswin32c"]
    test_run_args = ["--version"]
    supports_anamorphic = True

    def render(self, filename, page, res, antialias=True):
        imgfile = TempFileName + ".tif"
        aa_bits = (4 if antialias else 1)
        try:
            self.execute(["-q"] + GhostScriptPlatformOptions + [
                "-dBATCH", "-dNOPAUSE",
                "-sDEVICE=tiff24nc",
                "-dUseCropBox",
                "-sOutputFile=" + imgfile,
                "-dFirstPage=%d" % page,
                "-dLastPage=%d" % page,
                "-r%dx%d" % res,
                "-dTextAlphaBits=%d" % aa_bits,
                "-dGraphicsAlphaBits=%s" % aa_bits,
                filename
            ])
            return self.load(imgfile)
        finally:
            self.remove(imgfile)
AvailableRenderers.append(GhostScriptRenderer)

def InitPDFRenderer():
    global PDFRenderer
    if PDFRenderer:
        return PDFRenderer
    fail_reasons = []
    for r_class in AvailableRenderers:
        if not r_class.supports(PDFRendererPath):
            continue
        try:
            PDFRenderer = r_class(PDFRendererPath)
            print >>sys.stderr, "PDF renderer:", PDFRenderer.name
            return PDFRenderer
        except RendererUnavailable, e:
            if Verbose:
                print >>sys.stderr, "Not using %s for PDF rendering:" % r_class.name, e
            else:
                fail_reasons.append((r_class.name, str(e)))
    print >>sys.stderr, "ERROR: PDF renderer initialization failed."
    for item in fail_reasons:
        print >>sys.stderr, "       - %s: %s" % item
    print >>sys.stderr, "       Display of PDF files will not be supported."


# generate a dummy image
def DummyPage():
    img = Image.new('RGB', (ScreenWidth, ScreenHeight))
    img.paste(LogoImage, ((ScreenWidth  - LogoImage.size[0]) / 2,
                          (ScreenHeight - LogoImage.size[1]) / 2))
    return img

# load a page from a PDF file
def RenderPDF(page, MayAdjustResolution, ZoomMode):
    if not PDFRenderer:
        return DummyPage()

    # load props
    SourceFile = GetPageProp(page, '_file')
    RealPage = GetPageProp(page, '_page')
    OutputSizes = GetPageProp(page, '_out')
    if not OutputSizes:
        OutputSizes = GetFileProp(SourceFile, 'out', [(ScreenWidth + Overscan, ScreenHeight + Overscan), (ScreenWidth + Overscan, ScreenHeight + Overscan)])
        SetPageProp(page, '_out', OutputSizes)
    Resolutions = GetPageProp(page, '_res')
    if not Resolutions:
        Resolutions = GetFileProp(SourceFile, 'res', [(72.0, 72.0), (72.0, 72.0)])
        SetPageProp(page, '_res', Resolutions)
    rot = GetPageProp(page, 'rotate', Rotation)
    out = OutputSizes[rot & 1]
    res = Resolutions[rot & 1]
    zscale = 1

    # handle supersample and zoom mode
    use_aa = True
    if ZoomMode:
        res = (ZoomFactor * res[0], ZoomFactor * res[1])
        out = (ZoomFactor * out[0], ZoomFactor * out[1])
        zscale = ZoomFactor
    elif Supersample:
        res = (Supersample * res[0], Supersample * res[1])
        out = (Supersample * out[0], Supersample * out[1])
        use_aa = False

    # prepare the renderer options
    if PDFRenderer.supports_anamorphic:
        parscale = False
        useres = (int(res[0] + 0.5), int(res[1] + 0.5))
    else:
        parscale = (abs(1.0 - PAR) > 0.01)
        useres = max(res[0], res[1])
        res = (useres, useres)
        useres = int(useres + 0.5)
        useres = (useres, useres)

    # call the renderer
    try:
        img = PDFRenderer.render(SourceFile, RealPage, useres, use_aa)
    except RenderError, e:
        print >>sys.stderr, "ERROR: failed to render page %d:" % page, e
        return DummyPage()

    # apply rotation
    if rot: img = img.rotate(90 * (4 - rot))

    # compute final output image size based on PAR
    if not parscale:
        got = img.size
    elif PAR > 1.0:
        got = (int(img.size[0] / PAR + 0.5), img.size[1])
    else:
        got = (img.size[0], int(img.size[1] * PAR + 0.5))

    # if the image size is strange, re-adjust the rendering resolution
    tolerance = max(4, (ScreenWidth + ScreenHeight) / 400)
    if MayAdjustResolution and (max(abs(got[0] - out[0]), abs(got[1] - out[1])) >= tolerance):
        newout = ZoomToFit((img.size[0], img.size[1] * PAR))
        rscale = (float(newout[0]) / img.size[0], float(newout[1]) / img.size[1])
        if rot & 1:
            newres = (res[0] * rscale[1], res[1] * rscale[0])
        else:
            newres = (res[0] * rscale[0], res[1] * rscale[1])
        # only modify anything if the resolution deviation is large enough
        if max(abs(1.0 - newres[0] / res[0]), abs(1.0 - newres[1] / res[1])) > 0.05:
            # create a copy of the old values: they are lists and thus stored
            # in the PageProps as references; we don't want to influence other
            # pages though
            OutputSizes = OutputSizes[:]
            Resolutions = Resolutions[:]
            # modify the appropriate rotation slot
            OutputSizes[rot & 1] = newout
            Resolutions[rot & 1] = newres
            # store the new values for this page ...
            SetPageProp(page, '_out', OutputSizes)
            SetPageProp(page, '_res', Resolutions)
            # ... and as a default for the file as well (future pages are likely
            # to have the same resolution)
            SetFileProp(SourceFile, 'out', OutputSizes)
            SetFileProp(SourceFile, 'res', Resolutions)
            return RenderPDF(page, False, ZoomMode)

    # downsample a supersampled image
    if Supersample and not(ZoomMode):
        img = img.resize((int(float(out[0]) / Supersample + 0.5),
                          int(float(out[1]) / Supersample + 0.5)), Image.ANTIALIAS)
        parscale = False  # don't scale again

    # perform PAR scaling (required for pdftoppm which doesn't support different
    # dpi for horizontal and vertical)
    if parscale:
        if PAR > 1.0:
            img = img.resize((int(img.size[0] / PAR + 0.5), img.size[1]), Image.ANTIALIAS)
        else:
            img = img.resize((img.size[0], int(img.size[1] * PAR + 0.5)), Image.ANTIALIAS)

    # crop the overscan (if present)
    if Overscan:
        target = (ScreenWidth * zscale, ScreenHeight * zscale)
        scale = None
        if (img.size[1] > target[1]) and (img.size[0] < target[0]):
            scale = float(target[1]) / img.size[1]
        elif (img.size[0] > target[0]) and (img.size[1] < target[1]):
            scale = float(target[0]) / img.size[0]
        if scale:
            w = int(img.size[0] * scale + 0.5)
            h = int(img.size[1] * scale + 0.5)
            if (w <= img.size[0]) and (h <= img.size[1]):
                x0 = (img.size[0] - w) / 2
                y0 = (img.size[1] - h) / 2
                img = img.crop((x0, y0, x0 + w, y0 + h))

    return img


# load a page from an image file
def LoadImage(page, ZoomMode):
    # open the image file with PIL
    try:
        img = Image.open(GetPageProp(page, '_file'))
        img.load()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print >>sys.stderr, "Image file `%s' is broken." % GetPageProp(page, '_file')
        return DummyPage()

    # apply rotation
    rot = GetPageProp(page, 'rotate')
    if rot is None:
        rot = Rotation
    if rot:
        img = img.rotate(90 * (4 - rot))

    # determine destination size
    newsize = ZoomToFit((img.size[0], int(img.size[1] * PAR + 0.5)),
                        (ScreenWidth, ScreenHeight))
    # don't scale if the source size is too close to the destination size
    if abs(newsize[0] - img.size[0]) < 2: newsize = img.size
    # don't scale if the source is smaller than the destination
    if not(Scaling) and (newsize > img.size): newsize = img.size
    # zoom up (if wanted)
    if ZoomMode: newsize = (2 * newsize[0], 2 * newsize[1])
    # skip processing if there was no change
    if newsize == img.size: return img

    # select a nice filter and resize the image
    if newsize > img.size:
        filter = Image.BICUBIC
    else:
        filter = Image.ANTIALIAS
    return img.resize(newsize, filter)


# render a page to an OpenGL texture
def PageImage(page, ZoomMode=False, RenderMode=False):
    global OverviewNeedUpdate, HighQualityOverview
    EnableCacheRead = not(ZoomMode or RenderMode)
    EnableCacheWrite = EnableCacheRead and \
                       (page >= PageRangeStart) and (page <= PageRangeEnd)

    # check for the image in the cache
    if EnableCacheRead:
        data = GetCacheImage(page)
        if data: return data

    # if it's not in the temporary cache, render it
    Lrender.acquire()
    try:
        # check the cache again, because another thread might have just
        # rendered the page while we were waiting for the render lock
        if EnableCacheRead:
            data = GetCacheImage(page)
            if data: return data

        # retrieve the image from the persistent cache or fully re-render it
        if EnableCacheRead:
            img = GetPCacheImage(page)
        else:
            img = None
        if not img:
            if GetPageProp(page, '_page'):
                img = RenderPDF(page, not(ZoomMode), ZoomMode)
            else:
                img = LoadImage(page, ZoomMode)
            if GetPageProp(page, 'invert', InvertPages):
                img = ImageChops.invert(img)
            if EnableCacheWrite:
                AddToPCache(page, img)

        # create black background image to paste real image onto
        if ZoomMode:
            TextureImage = Image.new('RGB', (ZoomFactor * TexWidth, ZoomFactor * TexHeight))
            TextureImage.paste(img, ((ZoomFactor * ScreenWidth  - img.size[0]) / 2, \
                                     (ZoomFactor * ScreenHeight - img.size[1]) / 2))
        else:
            TextureImage = Image.new('RGB', (TexWidth, TexHeight))
            x0 = (ScreenWidth  - img.size[0]) / 2
            y0 = (ScreenHeight - img.size[1]) / 2
            TextureImage.paste(img, (x0, y0))
            SetPageProp(page, '_box', (x0, y0, x0 + img.size[0], y0 + img.size[1]))
            FixHyperlinks(page)

        # paste thumbnail into overview image
        if GetPageProp(page, ('overview', '_overview'), True) \
        and (page >= PageRangeStart) and (page <= PageRangeEnd) \
        and not(GetPageProp(page, '_overview_rendered')) \
        and not(RenderMode):
            pos = OverviewPos(OverviewPageMapInv[page])
            Loverview.acquire()
            try:
                # first, fill the underlying area with black (i.e. remove the dummy logo)
                blackness = Image.new('RGB', (OverviewCellX - OverviewBorder, \
                                              OverviewCellY - OverviewBorder))
                OverviewImage.paste(blackness, (pos[0] + OverviewBorder / 2, \
                                                pos[1] + OverviewBorder))
                del blackness
                # then, scale down the original image and paste it
                if HalfScreen:
                    img = img.crop((0, 0, img.size[0] / 2, img.size[1]))
                sx = OverviewCellX - 2 * OverviewBorder
                sy = OverviewCellY - 2 * OverviewBorder
                if HighQualityOverview:
                    t0 = time.time()
                    img.thumbnail((sx, sy), Image.ANTIALIAS)
                    if (time.time() - t0) > 0.5:
                        print >>sys.stderr, "Note: Your system seems to be quite slow; falling back to a faster,"
                        print >>sys.stderr, "      but slightly lower-quality overview page rendering mode"
                        HighQualityOverview = False
                else:
                    img.thumbnail((sx * 2, sy * 2), Image.NEAREST)
                    img.thumbnail((sx, sy), Image.BILINEAR)
                OverviewImage.paste(img, \
                   (pos[0] + (OverviewCellX - img.size[0]) / 2, \
                    pos[1] + (OverviewCellY - img.size[1]) / 2))
            finally:
                Loverview.release()
            SetPageProp(page, '_overview_rendered', True)
            OverviewNeedUpdate = True
        del img

        # return texture data
        if RenderMode:
            return TextureImage
        data = img2str(TextureImage)
        del TextureImage
    finally:
        Lrender.release()

    # finally add it back into the cache and return it
    if EnableCacheWrite:
        AddToCache(page, data)
    return data

# render a page to an OpenGL texture
def RenderPage(page, target):
    gl.BindTexture(gl.TEXTURE_2D, target)
    while gl.GetError():
        pass  # clear all OpenGL errors
    gl.TexImage2D(gl.TEXTURE_2D, 0, gl.RGB, TexWidth, TexHeight, 0, gl.RGB, gl.UNSIGNED_BYTE, PageImage(page))
    if gl.GetError():
        print >>sys.stderr, "I'm sorry, but your graphics card is not capable of rendering presentations"
        print >>sys.stderr, "in this resolution. Either the texture memory is exhausted, or there is no"
        print >>sys.stderr, "support for large textures (%dx%d). Please try to run Impressive in a" % (TexWidth, TexHeight)
        print >>sys.stderr, "smaller resolution using the -g command-line option."
        sys.exit(1)

# background rendering thread
def RenderThread(p1, p2):
    global RTrunning, RTrestart
    RTrunning = get_thread_id() or True
    RTrestart = True
    while RTrestart:
        RTrestart = False
        for pdf in FileProps:
            if not pdf.lower().endswith(".pdf"): continue
            if RTrestart: break
            SafeCall(ParsePDF, [pdf])
        if RTrestart: continue
        for page in xrange(1, PageCount + 1):
            if RTrestart: break
            if (page != p1) and (page != p2) \
            and (page >= PageRangeStart) and (page <= PageRangeEnd):
                SafeCall(PageImage, [page])
    RTrunning = False
    if CacheMode >= FileCache:
        print >>sys.stderr, "Background rendering finished, used %.1f MiB of disk space." %\
              (CacheFilePos / 1048576.0)
    elif CacheMode >= MemCache:
        print >>sys.stderr, "Background rendering finished, using %.1f MiB of memory." %\
              (sum(map(len, PageCache.itervalues())) / 1048576.0)


##### RENDER MODE ##############################################################

def DoRender():
    global TexWidth, TexHeight
    TexWidth = ScreenWidth
    TexHeight = ScreenHeight
    if os.path.exists(RenderToDirectory):
        print >>sys.stderr, "Destination directory `%s' already exists," % RenderToDirectory
        print >>sys.stderr, "refusing to overwrite anything."
        return 1
    try:
        os.mkdir(RenderToDirectory)
    except OSError, e:
        print >>sys.stderr, "Cannot create destination directory `%s':" % RenderToDirectory
        print >>sys.stderr, e.strerror
        return 1
    print >>sys.stderr, "Rendering presentation into `%s'" % RenderToDirectory
    for page in xrange(1, PageCount + 1):
        PageImage(page, RenderMode=True).save("%s/page%04d.png" % (RenderToDirectory, page))
        sys.stdout.write("[%d] " % page)
        sys.stdout.flush()
    print >>sys.stderr
    print >>sys.stderr, "Done."
    return 0
