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
        Platform.SetWindowTitle(caption)
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
    Platform.SetWindowTitle(caption)

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
    t0 = Platform.GetTicks()
    while BoxFadeDuration > 0:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BoxFadeDuration
        if t >= 1.0: break
        DrawCurrentPage(func(t))
    DrawCurrentPage(func(1.0))
    return 0

# reset the timer
def ResetTimer():
    global StartTime, PageEnterTime
    if TimeTracking and not(FirstPage):
        print "--- timer was reset here ---"
    StartTime = Platform.GetTicks()
    PageEnterTime = 0

# start video playback
def PlayVideo(video):
    global MPlayerProcess, VideoPlaying, NextPageAfterVideo
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
            opts += ["-wid", str(Platform.GetWindowID())]
        except KeyError:
            print >>sys.stderr, "Sorry, but Impressive only supports video on your operating system if fullscreen"
            print >>sys.stderr, "mode is used."
            VideoPlaying = False
            MPlayerProcess = None
            return
    if not isinstance(video, list):
        video = [video]
    NextPageAfterVideo = False
    try:
        MPlayerProcess = subprocess.Popen([MPlayerPath] + opts + video, stdin=subprocess.PIPE)
        if MPlayerColorKey:
            gl.Clear(gl.COLOR_BUFFER_BIT)
            Platform.SwapBuffers()
        VideoPlaying = True
    except OSError:
        MPlayerProcess = None

# called each time a page is entered, AFTER the transition, BEFORE entering box-fade mode
def PreparePage():
    global SpotRadius, SpotRadiusBase
    global BoxFadeDarkness, BoxFadeDarknessBase
    global BoxZoomDarkness, BoxZoomDarknessBase
    override = GetPageProp(Pcurrent, 'radius')
    if override:
        SpotRadius = override
        SpotRadiusBase = override
        GenerateSpotMesh()
    override = GetPageProp(Pcurrent, 'darkness')
    if override is not None:
        BoxFadeDarkness = override * 0.01
        BoxFadeDarknessBase = override * 0.01
    override = GetPageProp(Pcurrent, 'zoomdarkness')
    if override is not None:
        BoxZoomDarkness = override * 0.01
        BoxZoomDarknessBase = override * 0.01

# called each time a page is entered, AFTER the transition, AFTER entering box-fade mode
def PageEntered(update_time=True):
    global PageEnterTime, PageTimeout, MPlayerProcess, IsZoomed, WantStatus
    if update_time:
        PageEnterTime = Platform.GetTicks() - StartTime
    IsZoomed = 0  # no, we don't have a pre-zoomed image right now
    WantStatus = False  # don't show status unless it's changed interactively
    PageTimeout = AutoAdvance
    shown = GetPageProp(Pcurrent, '_shown', 0)
    try:
        os.chdir(os.path.dirname(GetPageProp(Pcurrent, '_file')))
    except OSError:
        pass
    if not(shown) or Wrap:
        PageTimeout = GetPageProp(Pcurrent, 'timeout', PageTimeout)
    if GetPageProp(Pcurrent, '_video'):
        PlayVideo(GetPageProp(Pcurrent, '_file'))
    if not(shown) or GetPageProp(Pcurrent, 'always', False):
        if not GetPageProp(Pcurrent, '_video'):
            video = GetPageProp(Pcurrent, 'video')
            sound = GetPageProp(Pcurrent, 'sound')
            PlayVideo(video)
            if sound and not(video):
                StopMPlayer()
                try:
                    MPlayerProcess = subprocess.Popen( \
                        [MPlayerPath, "-quiet", "-really-quiet", "-novideo", sound], \
                        stdin=subprocess.PIPE)
                except OSError:
                    MPlayerProcess = None
        SafeCall(GetPageProp(Pcurrent, 'OnEnterOnce'))
    SafeCall(GetPageProp(Pcurrent, 'OnEnter'))
    if PageTimeout:
        Platform.ScheduleEvent("$page-timeout", PageTimeout)
    SetPageProp(Pcurrent, '_shown', shown + 1)

# called each time a page is left
def PageLeft(overview=False):
    global FirstPage, LastPage, WantStatus, PageLeaveTime
    PageLeaveTime = Platform.GetTicks() - StartTime
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
        t1 = Platform.GetTicks() - StartTime
        dt = (t1 - PageEnterTime + 500) / 1000
        if overview:
            p = "over"
        else:
            p = "%4d" % Pcurrent
        print "%s%9s%9s%9s" % (p, FormatTime(dt), \
                                  FormatTime(PageEnterTime / 1000), \
                                  FormatTime(t1 / 1000))

# create an instance of a transition class
def InstantiateTransition(trans_class):
    try:
        return trans_class()
    except GLInvalidShaderError:
        return None
    except GLShaderCompileError:
        print >>sys.stderr, "Note: all %s transitions will be disabled" % trans_class.__name__
        return None

# perform a transition to a specified page
def TransitionTo(page, allow_transition=True):
    global Pcurrent, Pnext, Tcurrent, Tnext
    global PageCount, Marking, Tracing, Panning
    global TransitionRunning, TransitionPhase

    # first, stop video and kill the auto-timer
    if VideoPlaying:
        StopMPlayer()
    Platform.ScheduleEvent("$page-timeout", 0)

    # invalid page? go away
    if not PreloadNextPage(page):
        if QuitAtEnd:
            LeaveZoomMode(allow_transition)
            if FadeInOut:
                EnterFadeMode()
            PageLeft()
            Quit()
        return 0

    # leave zoom mode now, if enabled
    LeaveZoomMode(allow_transition)

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
    tpage = max(Pcurrent, Pnext)
    trans = None
    if allow_transition:
        trans = GetPageProp(tpage, 'transition', GetPageProp(tpage, '_transition'))
    else:
        trans = None
    if trans is not None:
        transtime = GetPageProp(tpage, 'transtime', TransitionDuration)
        try:
            dummy = trans.__class__
        except AttributeError:
            # ah, gotcha! the transition is not yet instantiated!
            trans = InstantiateTransition(trans)
            PageProps[tpage][tkey] = trans
    if trans is None:
        transtime = 0

    # backward motion? then swap page buffers now
    backward = (Pnext < Pcurrent)
    if Wrap and (min(Pcurrent, Pnext) == 1) and (max(Pcurrent, Pnext) == PageCount):
        backward = not(backward)  # special case: last<->first in wrap mode
    if backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # transition animation
    if not(skip) and transtime:
        transtime = 1.0 / transtime
        TransitionRunning = True
        trans.start()
        t0 = Platform.GetTicks()
        while not(VideoPlaying):
            if Platform.CheckAnimationCancelEvent():
                skip = 1
                break
            t = (Platform.GetTicks() - t0) * transtime
            if t >= 1.0: break
            TransitionPhase = t
            if backward: t = 1.0 - t
            gl.Clear(gl.COLOR_BUFFER_BIT)
            trans.render(t)
            DrawOverlays(t)
            Platform.SwapBuffers()
        TransitionRunning = False

    # forward motion => swap page buffers now
    if not backward:
        Pcurrent, Pnext = (Pnext, Pcurrent)
        Tcurrent, Tnext = (Tnext, Tcurrent)

    # prepare the page's changeable metadata
    PreparePage()

    # box fade-in
    if not(skip) and GetPageProp(Pcurrent, 'boxes'): BoxFade(lambda t: t)

    # finally update the screen and preload the next page
    DrawCurrentPage()
    PageEntered()
    if not PreloadNextPage(GetNextPage(Pcurrent, 1)):
        PreloadNextPage(GetNextPage(Pcurrent, -1))
    return 1

# zoom mode animation
def ZoomAnimation(targetx, targety, func, duration_override=None):
    global ZoomX0, ZoomY0, ZoomArea
    t0 = Platform.GetTicks()
    if duration_override is None:
        duration = ZoomDuration
    else:
        duration = duration_override
    while duration > 0:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / duration
        if t >= 1.0: break
        t = func(t)
        dark = (t if BoxZoom else 1.0)
        t = (2.0 - t) * t
        ZoomX0 = targetx * t
        ZoomY0 = targety * t
        ZoomArea = 1.0 - (1.0 - 1.0 / ViewZoomFactor) * t
        DrawCurrentPage(dark=dark)
    t = func(1.0)
    ZoomX0 = targetx * t
    ZoomY0 = targety * t
    ZoomArea = 1.0 - (1.0 - 1.0 / ViewZoomFactor) * t
    GenerateSpotMesh()
    DrawCurrentPage(dark=(t if BoxZoom else 1.0))

# enter zoom mode
def EnterZoomMode(factor, targetx, targety):
    global ZoomMode, ViewZoomFactor, ResZoomFactor, IsZoomed, HighResZoomFailed
    ViewZoomFactor = factor
    ResZoomFactor = min(factor, MaxZoomFactor)
    ZoomAnimation(targetx, targety, lambda t: t)
    ZoomMode = True
    if (IsZoomed >= ResZoomFactor) or (ResZoomFactor < 1.1) or HighResZoomFailed:
        return
    gl.BindTexture(gl.TEXTURE_2D, Tcurrent)
    while gl.GetError():
        pass  # clear all OpenGL errors
    gl.TexImage2D(gl.TEXTURE_2D, 0, gl.RGB, int(ResZoomFactor * TexWidth), int(ResZoomFactor * TexHeight), 0, gl.RGB, gl.UNSIGNED_BYTE, PageImage(Pcurrent, True))
    if gl.GetError():
        print >>sys.stderr, "I'm sorry, but your graphics card is not capable of rendering presentations"
        print >>sys.stderr, "in this resolution. Either the texture memory is exhausted, or there is no"
        print >>sys.stderr, "support for large textures (%dx%d). Please try to run Impressive in a" % (TexWidth, TexHeight)
        print >>sys.stderr, "smaller resolution using the -g command-line option."
        HighResZoomFailed = True
        return
    DrawCurrentPage()
    IsZoomed = ResZoomFactor

# leave zoom mode (if enabled)
def LeaveZoomMode(allow_transition=True):
    global ZoomMode, BoxZoom, Panning, ViewZoomFactor, ResZoomFactor
    if not ZoomMode: return
    ZoomAnimation(ZoomX0, ZoomY0, lambda t: 1.0 - t, (None if allow_transition else 0))
    ZoomMode = False
    BoxZoom = False
    Panning = False
    ViewZoomFactor = 1
    ResZoomFactor = 1

# check whether a box mark is too small
def BoxTooSmall():
    return ((abs(MarkUL[0] - MarkLR[0]) * ScreenWidth)  < MinBoxSize) \
        or ((abs(MarkUL[1] - MarkLR[1]) * ScreenHeight) < MinBoxSize)

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
                PageProps[page][key] = InstantiateTransition(trans)

# update timer values and screen timer
def TimerTick():
    global CurrentTime, ProgressBarPos
    redraw = False
    newtime = (Platform.GetTicks() - StartTime) * 0.001
    if EstimatedDuration:
        newpos = int(ScreenWidth * newtime / EstimatedDuration)
        if newpos != ProgressBarPos:
            redraw = True
        ProgressBarPos = newpos
    newtime = int(newtime)
    if TimeDisplay and (CurrentTime != newtime):
        redraw = True
    if PageTimeout and AutoAdvanceProgress:
        redraw = True
    CurrentTime = newtime
    return redraw

# enables time tracking mode (if not already done so)
def EnableTimeTracking(force=False):
    global TimeTracking
    if force or (TimeDisplay and not(TimeTracking) and not(ShowClock) and FirstPage):
        print >>sys.stderr, "Time tracking mode enabled."
        TimeTracking = True
        print "page duration    enter    leave"
        print "---- -------- -------- --------"

# set cursor visibility
def SetCursor(visible):
    global CursorVisible
    CursorVisible = visible
    if EnableCursor and not(CursorImage) and (MouseHideDelay != 1):
        Platform.SetMouseVisible(visible)

# handle a shortcut key event: store it (if shifted) or return the
# page number to navigate to (if not)
def HandleShortcutKey(key, current=0):
    if not(key) or (key[0] != '*'):
        return None
    shift = key.startswith('*shift+')
    if shift:
        key = key[7:]
    else:
        key = key[1:]
    if (len(key) == 1) or ((key >= "f1") and (key <= "f9")):
        # Note: F10..F12 are implicitly included due to lexicographic sorting
        page = None
        for check_page, props in PageProps.iteritems():
            if props.get('shortcut') == key:
                page = check_page
                break
        if shift:
            if page:
                DelPageProp(page, 'shortcut')
            SetPageProp(current, 'shortcut', key)
        elif page and (page != current):
            return page
    return None
