##### PAGE RENDERING ###########################################################

# generate a dummy image
def DummyPage():
    img = Image.new('RGB', (ScreenWidth, ScreenHeight))
    img.paste(LogoImage, ((ScreenWidth  - LogoImage.size[0]) / 2,
                          (ScreenHeight - LogoImage.size[1]) / 2))
    return img

# load a page from a PDF file
def RenderPDF(page, MayAdjustResolution, ZoomMode):
    global UseGhostScript
    UseGhostScriptOnce = False

    # load props
    SourceFile = GetPageProp(page, '_file')
    RealPage = GetPageProp(page, '_page')
    OutputSizes = GetFileProp(SourceFile, 'out', [(ScreenWidth, ScreenHeight), (ScreenWidth, ScreenHeight)])
    Resolutions = GetFileProp(SourceFile, 'res', [(72.0, 72.0), (72.0, 72.0)])
    rot = GetPageProp(page, 'rotate')
    if rot is None: rot = Rotation
    out = OutputSizes[rot & 1]
    res = Resolutions[rot & 1]

    # handle supersample and zoom mode
    if Supersample and not(ZoomMode):
        AlphaBits = 1
    else:
        AlphaBits = 4
    if ZoomMode:
        res = (ZoomFactor * res[0], ZoomFactor * res[1])
        out = (ZoomFactor * out[0], ZoomFactor * out[1])
    elif Supersample:
        res = (Supersample * res[0], Supersample * res[1])
        out = (Supersample * out[0], Supersample * out[1])
    parscale = False

    # call pdftoppm to generate the page image
    if not UseGhostScript:
        renderer = "pdftoppm"
        try:
            useres = max(res[0], res[1])
            assert 0 == spawn(os.P_WAIT, \
                pdftoppmPath, ["pdftoppm", "-q"] + [ \
                "-f", str(RealPage), "-l", str(RealPage),
                "-r", str(int(useres + 0.5)),
                FileNameEscape + SourceFile + FileNameEscape,
                TempFileName])
            if abs(1.0 - PAR) > 0.01:
                parscale = True
            res = (useres, useres)
            # determine output filename
            digits = GetFileProp(SourceFile, 'digits', 6)
            imgfile = TempFileName + ("-%%0%dd.ppm" % digits) % RealPage
            if not os.path.exists(imgfile):
                for digits in xrange(6, 0, -1):
                    imgfile = TempFileName + ("-%%0%dd.ppm" % digits) % RealPage
                    if os.path.exists(imgfile): break
                SetFileProp(SourceFile, 'digits', digits)
        except OSError, (errcode, errmsg):
            print >>sys.stderr, "Warning: Cannot start pdftoppm -", errmsg
            print >>sys.stderr, "Falling back to GhostScript (permanently)."
            UseGhostScript = True
        except AssertionError:
            print >>sys.stderr, "There was an error while rendering page %d" % page
            print >>sys.stderr, "Falling back to GhostScript for this page."
            UseGhostScriptOnce = True

    # fallback to GhostScript
    if UseGhostScript or UseGhostScriptOnce:
        imgfile = TempFileName + ".tif"
        renderer = "GhostScript"
        try:
            assert 0 == spawn(os.P_WAIT, \
                GhostScriptPath, ["gs", "-q"] + GhostScriptPlatformOptions + [ \
                "-dBATCH", "-dNOPAUSE", "-sDEVICE=tiff24nc", "-dUseCropBox",
                "-sOutputFile=" + imgfile, \
                "-dFirstPage=%d" % RealPage, "-dLastPage=%d" % RealPage,
                "-r%dx%d" % (int(res[0] + 0.5), int(res[1] + 0.5)), \
                "-dTextAlphaBits=%d" % AlphaBits, \
                "-dGraphicsAlphaBits=%s" % AlphaBits, \
                FileNameEscape + SourceFile + FileNameEscape])
        except OSError, (errcode, errmsg):
            print >>sys.stderr, "Error: Cannot start GhostScript -", errmsg
            return DummyPage()
        except AssertionError:
            print >>sys.stderr, "There was an error while rendering page %d" % page
            return DummyPage()

    # open the page image file with PIL
    try:
        img = Image.open(imgfile)
        img.load()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print >>sys.stderr, "Error: %s produced an unreadable file (page %d)" % (renderer, page)
        return DummyPage()

    # try to delete the file again (this constantly fails on Win32 ...)
    try:
        os.remove(imgfile)
    except OSError:
        pass

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
        if max(abs(1.0 - newres[0] / res[0]), abs(1.0 - newres[1] / res[1])) > 0.05:
            # only modify anything if the resolution deviation is large enough
            OutputSizes[rot & 1] = newout
            Resolutions[rot & 1] = newres
            SetFileProp(SourceFile, 'out', OutputSizes)
            SetFileProp(SourceFile, 'res', Resolutions)
            return RenderPDF(page, False, ZoomMode)

    # downsample a supersampled image
    if Supersample and not(ZoomMode):
        if Supersample and not(ZoomMode):
            w = out[0] / Supersample
            h = out[1] / Supersample
        else:
            w, h = out
        return img.resize((int(w + 0.5), int(h + 0.5)), Image.ANTIALIAS)

    # perform PAR scaling (required for pdftoppm which doesn't support different
    # dpi for horizontal and vertical)
    if parscale:
        if PAR > 1.0:
            return img.resize((int(img.size[0] / PAR + 0.5), img.size[1]), Image.ANTIALIAS)
        else:
            return img.resize((img.size[0], int(img.size[1] * PAR + 0.5)), Image.ANTIALIAS)

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
        print >>sys.stderr, "Image file `%s' is broken." % (FileList[page - 1])
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
    global OverviewNeedUpdate
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
                img.thumbnail((OverviewCellX - 2 * OverviewBorder, \
                               OverviewCellY - 2 * OverviewBorder), \
                               Image.ANTIALIAS)
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
        data=TextureImage.tostring()
        del TextureImage
    finally:
      Lrender.release()

    # finally add it back into the cache and return it
    if EnableCacheWrite:
        AddToCache(page, data)
    return data

# render a page to an OpenGL texture
def RenderPage(page, target):
    glBindTexture(TextureTarget, target)
    try:
        glTexImage2D(TextureTarget, 0, 3, TexWidth, TexHeight, 0,\
                     GL_RGB, GL_UNSIGNED_BYTE, PageImage(page))
    except GLerror:
        print >>sys.stderr, "I'm sorry, but your graphics card is not capable of rendering presentations"
        print >>sys.stderr, "in this resolution. Either the texture memory is exhausted, or there is no"
        print >>sys.stderr, "support for large textures (%dx%d). Please try to run Impressive in a" % (TexWidth, TexHeight)
        print >>sys.stderr, "smaller resolution using the -g command-line option."
        sys.exit(1)

# background rendering thread
def RenderThread(p1, p2):
    global RTrunning, RTrestart
    RTrunning = True
    RTrestart = True
    while RTrestart:
        RTrestart = False
        for pdf in FileProps:
            if not pdf.lower().endswith(".pdf"): continue
            if RTrestart: break
            ParsePDF(pdf)
        if RTrestart: continue
        for page in xrange(1, PageCount + 1):
            if RTrestart: break
            if (page != p1) and (page != p2) \
            and (page >= PageRangeStart) and (page <= PageRangeEnd):
                PageImage(page)
    RTrunning = False
    if CacheMode >= FileCache:
        print >>sys.stderr, "Background rendering finished, used %.1f MiB of disk space." %\
              (CacheFilePos / 1048576.0)


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
