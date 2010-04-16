##### CONTROL AND NAVIGATION ###################################################

# update the applications' title bar
def UpdateCaption(page=0, force=False):
    global CurrentCaption, CurrentOSDCaption, CurrentOSDPage, CurrentOSDStatus
    global CurrentOSDComment
    if (page == CurrentCaption) and not(force):
        return
    CurrentCaption = page
    caption = __title__
    if DocumentTitle:
        caption += " - " + DocumentTitle
    if page < 1:
        CurrentOSDCaption = ""
        CurrentOSDPage = ""
        CurrentOSDStatus = ""
        CurrentOSDComment = ""
        pygame.display.set_caption(caption, __title__)
        return
    CurrentOSDPage = "%d/%d" % (page, PageCount)
    caption = "%s (%s)" % (caption, CurrentOSDPage)
    title = GetPageProp(page, 'title') or GetPageProp(page, '_title')
    if title:
        caption += ": %s" % title
        CurrentOSDCaption = title
    else:
        CurrentOSDCaption = ""
    status = []
    if GetPageProp(page, 'skip', False):
        status.append("skipped: yes")
    if not GetPageProp(page, ('overview', '_overview'), True):
        status.append("on overview page: no")
    CurrentOSDStatus = ", ".join(status)
    CurrentOSDComment = GetPageProp(page, 'comment')
    pygame.display.set_caption(caption, __title__)

# get next/previous page
def GetNextPage(page, direction):
    try_page = page
    while True:
        try_page += direction
        if try_page == page:
            return 0  # tried all pages, but none found
        if Wrap:
            if try_page < 1: try_page = PageCount
            if try_page > PageCount: try_page = 1
        else:
            if try_page < 1 or try_page > PageCount:
                return 0  # start or end of presentation
        if not GetPageProp(try_page, 'skip', False):
            return try_page

# pre-load the following page into Pnext/Tnext
def PreloadNextPage(page):
    global Pnext, Tnext
    if (page < 1) or (page > PageCount):
        Pnext = 0
        return 0
    if page == Pnext:
        return 1
    RenderPage(page, Tnext)
    Pnext = page
    return 1

# perform box fading; the fade animation time is mapped through func()
def BoxFade(func):
    t0 = pygame.time.get_ticks()
    while 1:
        if pygame.event.get([KEYDOWN,MOUSEBUTTONUP]): break
        t = (pygame.time.get_ticks() - t0) * 1.0 / BoxFadeDuration
        if t >= 1.0: break
        DrawCurrentPage(func(t))
    DrawCurrentPage(func(1.0))
    return 0

# reset the timer
def ResetTimer():
    global StartTime, PageEnterTime
    if TimeTracking and not(FirstPage):
        print "--- timer was reset here ---"
    StartTime = pygame.time.get_ticks()
    PageEnterTime = 0

# start video playback
def PlayVideo(video):
    global MPlayerProcess, VideoPlaying
    if not video: return
    StopMPlayer()
    opts = ["-quiet", "-slave", \
            "-monitorpixelaspect", "1:1", \
            "-autosync", "100"] + \
            MPlayerPlatformOptions
    if Fullscreen:
        opts += ["-fs"]
    else:
        try:
            opts += ["-wid", str(pygame.display.get_wm_info()['window'])]
        except KeyError:
            print >>sys.stderr, "Sorry, but Impressive only supports video on your operating system if fullscreen"
            print >>sys.stderr, "mode is used."
            VideoPlaying = False
            MPlayerProcess = None
            return
    opts += [FileNameEscape + video + FileNameEscape]
    try:
        MPlayerProcess = subprocess.Popen([MPlayerPath] + opts, stdin=subprocess.PIPE)
        if MPlayerColorKey:
            glClear(GL_COLOR_BUFFER_BIT)
            pygame.display.flip()
        VideoPlaying = True
    except OSError:
        MPlayerProcess = None

# called each time a page is entered
def PageEntered(update_time=True):
    global PageEnterTime, MPlayerProcess, IsZoomed, WantStatus
    if update_time:
        PageEnterTime = pygame.time.get_ticks() - StartTime
    IsZoomed = False  # no, we don't have a pre-zoomed image right now
    WantStatus = False  # don't show status unless it's changed interactively
    timeout = AutoAdvance
    shown = GetPageProp(Pcurrent, '_shown', 0)
    if not(shown) or Wrap:
        timeout = GetPageProp(Pcurrent, 'timeout', timeout)
    if not(shown) or GetPageProp(Pcurrent, 'always', False):
        video = GetPageProp(Pcurrent, 'video')
        sound = GetPageProp(Pcurrent, 'sound')
        PlayVideo(video)
        if sound and not(video):
            StopMPlayer()
            try:
                MPlayerProcess = subprocess.Popen( \
                    [MPlayerPath, "-quiet", "-really-quiet", "-novideo", \
                     FileNameEscape + sound + FileNameEscape], \
                    stdin=subprocess.PIPE)
            except OSError:
                MPlayerProcess = None
        SafeCall(GetPageProp(Pcurrent, 'OnEnterOnce'))
    SafeCall(GetPageProp(Pcurrent, 'OnEnter'))
    if timeout: pygame.time.set_timer(USEREVENT_PAGE_TIMEOUT, timeout)
    SetPageProp(Pcurrent, '_shown', shown + 1)

# called each time a page is left
def PageLeft(overview=False):
    global FirstPage, LastPage, WantStatus
    WantStatus = False
    if not overview:
        if GetTristatePageProp(Pcurrent, 'reset'):
            ResetTimer()
        FirstPage = False
        LastPage = Pcurrent
        if GetPageProp(Pcurrent, '_shown', 0) == 1:
            SafeCall(GetPageProp(Pcurrent, 'OnLeaveOnce'))
        SafeCall(GetPageProp(Pcurrent, 'OnLeave'))
    if TimeTracking:
        t1 = pygame.time.get_ticks() - StartTime
        dt = (t1 - PageEnterTime + 500) / 1000
        if overview:
            p = "over"
        else:
            p = "%4d" % Pcurrent
        print "%s%9s%9s%9s" % (p, FormatTime(dt), \
                                  FormatTime(PageEnterTime / 1000), \
                                  FormatTime(t1 / 1000))

# perform a transition to a specified page
def TransitionTo(page):
    global Pcurrent, Pnext, Tcurrent, Tnext
    global PageCount, Marking, Tracing, Panning, TransitionRunning

    # first, stop video and kill the auto-timer
    if VideoPlaying:
        StopMPlayer()
    pygame.time.set_timer(USEREVENT_PAGE_TIMEOUT, 0)

    # invalid page? go away
    if not PreloadNextPage(page):
        return 0

    # notify that the page has been left
    PageLeft()

    # box fade-out
    if GetPageProp(Pcurrent, 'boxes') or Tracing:
        skip = BoxFade(lambda t: 1.0 - t)
    else:
        skip = 0

    # some housekeeping
    Marking = False
    Tracing = False
    UpdateCaption(page)

    # check if the transition is valid
    tpage = min(Pcurrent, Pnext)
    if 'transition' in PageProps[tpage]:
        tkey = 'transition'
    else:
        tkey = '_transition'
    trans = PageProps[tpage][tkey]
    if trans is None:
        transtime = 0
    else:
        transtime = GetPageProp(tpage, 'transtime', TransitionDuration)
        try:
            dummy = trans.__class__
        except AttributeError:
            # ah, gotcha! the transition is not yet intantiated!
            trans = trans()
            PageProps[tpage][tkey] = trans

    # backward motion? then swap page buffers now
    backward = (Pnext < Pcurrent)
    if backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # transition animation
    if not(skip) and transtime:
        transtime = 1.0 / transtime
        TransitionRunning = True
        t0 = pygame.time.get_ticks()
        while not(VideoPlaying):
            if pygame.event.get([KEYDOWN,MOUSEBUTTONUP]):
                skip = 1
                break
            t = (pygame.time.get_ticks() - t0) * transtime
            if t >= 1.0: break
            if backward: t = 1.0 - t
            glEnable(TextureTarget)
            trans.render(t)
            DrawOverlays(t)
            pygame.display.flip()
        TransitionRunning = False

    # forward motion => swap page buffers now
    if not backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # box fade-in
    if not(skip) and GetPageProp(Pcurrent, 'boxes'): BoxFade(lambda t: t)

    # finally update the screen and preload the next page
    DrawCurrentPage() # I do that twice because for some strange reason, the
    PageEntered()
    if not PreloadNextPage(GetNextPage(Pcurrent, 1)):
        PreloadNextPage(GetNextPage(Pcurrent, -1))
    return 1

# zoom mode animation
def ZoomAnimation(targetx, targety, func):
    global ZoomX0, ZoomY0, ZoomArea
    t0 = pygame.time.get_ticks()
    while True:
        if pygame.event.get([KEYDOWN,MOUSEBUTTONUP]): break
        t = (pygame.time.get_ticks() - t0) * 1.0 / ZoomDuration
        if t >= 1.0: break
        t = func(t)
        t = (2.0 - t) * t
        ZoomX0 = targetx * t
        ZoomY0 = targety * t
        ZoomArea = 1.0 - (1.0 - 1.0 / ZoomFactor) * t
        DrawCurrentPage()
    t = func(1.0)
    ZoomX0 = targetx * t
    ZoomY0 = targety * t
    ZoomArea = 1.0 - (1.0 - 1.0 / ZoomFactor) * t
    GenerateSpotMesh()
    DrawCurrentPage()

# enter zoom mode
def EnterZoomMode(targetx, targety):
    global ZoomMode, IsZoomed, ZoomWarningIssued
    ZoomAnimation(targetx, targety, lambda t: t)
    ZoomMode = True
    if TextureTarget != GL_TEXTURE_2D:
        if not ZoomWarningIssued:
            print >>sys.stderr, "Sorry, but I can't increase the detail level in zoom mode any further when"
            print >>sys.stderr, "GL_ARB_texture_rectangle is used. Please try running Impressive with the"
            print >>sys.stderr, "'-e' parameter. If a modern nVidia or ATI graphics card is used, a driver"
            print >>sys.stderr, "update may also fix the problem."
            ZoomWarningIssued = True
        return
    if not(HaveNPOT) and (npot(ZoomFactor) != ZoomFactor):
        if not ZoomWarningIssued:
            print >>sys.stderr, "Sorry, but I can't increase the detail level in zoom mode any further when"
            print >>sys.stderr, "conventional power-of-two textures are used and the zoom factor is not a"
            print >>sys.stderr, "power of two. Please use another zoom factor or a current graphics card"
            print >>sys.stderr, "with current drivers."
            ZoomWarningIssued = True
        return        
    if IsZoomed:
        return
    glBindTexture(TextureTarget, Tcurrent)
    try:
        glTexImage2D(TextureTarget, 0, 3, ZoomFactor * TexWidth, ZoomFactor * TexHeight, 0, \
                     GL_RGB, GL_UNSIGNED_BYTE, PageImage(Pcurrent, True))
    except GLerror:
        if not ZoomWarningIssued:
            print >>sys.stderr, "Sorry, but I can't increase the detail level in zoom mode any further, because"
            print >>sys.stderr, "your OpenGL implementation does not support that. Either the texture memory is"
            print >>sys.stderr, "exhausted, or there is no support for large textures (%dx%d). If you really" \
                  % (ZoomFactor * TexWidth, ZoomFactor * TexHeight)
            print >>sys.stderr, "need high-res zooming, please try to run Impressive in a smaller resolution"
            print >>sys.stderr, "or use a lower zoom factor."
            ZoomWarningIssued = True
        return
    DrawCurrentPage()
    IsZoomed = True

# leave zoom mode (if enabled)
def LeaveZoomMode():
    global ZoomMode
    if not ZoomMode: return
    ZoomAnimation(ZoomX0, ZoomY0, lambda t: 1.0 - t)
    ZoomMode = False
    Panning = False

# increment/decrement spot radius
def IncrementSpotSize(delta):
    global SpotRadius
    if not Tracing:
        return
    SpotRadius = max(SpotRadius + delta, 8)
    GenerateSpotMesh()
    DrawCurrentPage()

# post-initialize the page transitions
def PrepareTransitions():
    Unspecified = 0xAFFED00F
    # STEP 1: randomly assign transitions where the user didn't specify them
    cnt = sum([1 for page in xrange(1, PageCount + 1) \
               if GetPageProp(page, 'transition', Unspecified) == Unspecified])
    newtrans = ((cnt / len(AvailableTransitions) + 1) * AvailableTransitions)[:cnt]
    random.shuffle(newtrans)
    for page in xrange(1, PageCount + 1):
        if GetPageProp(page, 'transition', Unspecified) == Unspecified:
            SetPageProp(page, '_transition', newtrans.pop())
    # STEP 2: instantiate transitions
    for page in PageProps:
        for key in ('transition', '_transition'):
            if not key in PageProps[page]:
                continue
            trans = PageProps[page][key]
            if trans is not None:
                PageProps[page][key] = trans()

# update timer values and screen timer
def TimerTick():
    global CurrentTime, ProgressBarPos
    redraw = False
    newtime = (pygame.time.get_ticks() - StartTime) * 0.001
    if EstimatedDuration:
        newpos = int(ScreenWidth * newtime / EstimatedDuration)
        if newpos != ProgressBarPos:
            redraw = True
        ProgressBarPos = newpos
    newtime = int(newtime)
    if TimeDisplay and (CurrentTime != newtime):
        redraw = True
    CurrentTime = newtime
    return redraw

# set cursor visibility
def SetCursor(visible):
    global CursorVisible
    CursorVisible = visible
    if not CursorImage:
        pygame.mouse.set_visible(visible)

# shortcut handling
def IsValidShortcutKey(key):
    return ((key >= K_a)  and (key <= K_z)) \
        or ((key >= K_0)  and (key <= K_9)) \
        or ((key >= K_F1) and (key <= K_F12))
def FindShortcut(shortcut):
    for page, props in PageProps.iteritems():
        try:
            check = props['shortcut']
            if type(check) != types.StringType:
                check = int(check)
            elif (len(check) > 1) and (check[0] in "Ff"):
                check = K_F1 - 1 + int(check[1:])
            else:
                check = ord(check.lower())
        except (KeyError, TypeError, ValueError):
            continue
        if check == shortcut:
            return page
    return None
def AssignShortcut(page, key):
    old_page = FindShortcut(key)
    if old_page:
        del PageProps[old_page]['shortcut']
    if key < 127:
        shortcut = chr(key)
    elif (key >= K_F1) and (key <= K_F15):
        shortcut = "F%d" % (key - K_F1 + 1)
    else:
        shortcut = int(key)
    SetPageProp(page, 'shortcut', shortcut)
