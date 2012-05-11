##### EVENT HANDLING ###########################################################

# set fullscreen mode
def SetFullscreen(fs, do_init=True):
    global Fullscreen

    # let pygame do the real work
    if do_init:
        if fs == Fullscreen: return
        if not pygame.display.toggle_fullscreen(): return
    Fullscreen=fs

    # redraw the current page (pygame is too lazy to send an expose event ...)
    DrawCurrentPage()

    # show cursor and set auto-hide timer
    if fs:
        pygame.time.set_timer(USEREVENT_HIDE_MOUSE, MouseHideDelay)
    else:
        pygame.time.set_timer(USEREVENT_HIDE_MOUSE, 0)
        SetCursor(True)

# PageProp toggle
def TogglePageProp(prop, default):
    global WantStatus
    SetPageProp(Pcurrent, prop, not(GetPageProp(Pcurrent, prop, default)))
    UpdateCaption(Pcurrent, force=True)
    WantStatus = True
    DrawCurrentPage()

# main event handling function
def HandleEvent(event):
    global HaveMark, ZoomMode, Marking, Tracing, Panning, SpotRadius, FileStats
    global MarkUL, MarkLR, MouseDownX, MouseDownY, PanAnchorX, PanAnchorY
    global ZoomX0, ZoomY0, RTrunning, RTrestart, StartTime, PageEnterTime
    global CurrentTime, TimeDisplay, TimeTracking, ProgressBarPos

    if event.type == QUIT:
        if FadeInOut:
            EnterFadeMode()
        PageLeft()
        Quit()
    elif event.type == VIDEOEXPOSE:
        DrawCurrentPage()

    elif event.type == KEYDOWN:
        if VideoPlaying:
            try:
                if event.key in (K_ESCAPE, K_RETURN, u'q'):
                    StopMPlayer()
                    DrawCurrentPage()
                elif event.unicode == u' ':
                    MPlayerProcess.stdin.write('pause\n')
                elif event.unicode == u'.':
                    MPlayerProcess.stdin.write('frame_step\n')
                elif event.key == K_LEFT:
                    MPlayerProcess.stdin.write('seek -1 pausing_keep\n')
                elif event.key == K_RIGHT:
                    MPlayerProcess.stdin.write('seek 1 pausing_keep\n')                
                elif event.key == K_UP:
                    MPlayerProcess.stdin.write('seek 10 pausing_keep\n')
                elif event.key == K_DOWN:
                    MPlayerProcess.stdin.write('seek -10 pausing_keep\n')                
            except:
                StopMPlayer()
                DrawCurrentPage()
        elif (event.key == K_ESCAPE) or (event.unicode == u'q'):
            pygame.event.post(pygame.event.Event(QUIT))
        elif event.unicode == u'f':
            SetFullscreen(not Fullscreen)
        elif (event.key == K_TAB) and (event.mod & KMOD_ALT) and Fullscreen:
            SetFullscreen(False)
        elif event.unicode == u's':
            SaveInfoScript(InfoScriptPath)
        elif event.unicode == u'z':  # handle QWERTY and QWERTZ keyboards
            if ZoomMode:
                LeaveZoomMode()
            else:
                tx, ty = MouseToScreen(pygame.mouse.get_pos())
                EnterZoomMode((1.0 - 1.0 / ZoomFactor) * tx, \
                              (1.0 - 1.0 / ZoomFactor) * ty)
        elif event.unicode in (u'b', u'.'):
            FadeMode(0.0)
        elif event.unicode in (u'w', u','):
            FadeMode(1.0)
        elif event.unicode == u't':
            TimeDisplay = not(TimeDisplay)
            DrawCurrentPage()
            if TimeDisplay and not(TimeTracking) and FirstPage:
                print >>sys.stderr, "Time tracking mode enabled."
                TimeTracking = True
                print "page duration    enter    leave"
                print "---- -------- -------- --------"
        elif event.unicode == u'r':
            ResetTimer()
            if TimeDisplay: DrawCurrentPage()
        elif event.unicode == u'l':
            TransitionTo(LastPage)
        elif event.unicode == u'o':
            TogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))
        elif event.unicode == u'i':
            TogglePageProp('skip', False)
        elif event.key == K_TAB:
            LeaveZoomMode()
            DoOverview()
        elif event.key in (32, K_DOWN, K_RIGHT, K_PAGEDOWN):
            LeaveZoomMode()
            TransitionTo(GetNextPage(Pcurrent, 1))
        elif event.key in (K_BACKSPACE, K_UP, K_LEFT, K_PAGEUP):
            LeaveZoomMode()
            TransitionTo(GetNextPage(Pcurrent, -1))
        elif event.key == K_HOME:
            if Pcurrent != 1:
                TransitionTo(1)
        elif event.key == K_END:
            if Pcurrent != PageCount:
                TransitionTo(PageCount)
        elif event.key in (K_RETURN, K_KP_ENTER):
            if not(GetPageProp(Pcurrent, 'boxes')) and Tracing:
                BoxFade(lambda t: 1.0 - t)
            Tracing = not(Tracing)
            if not(GetPageProp(Pcurrent, 'boxes')) and Tracing:
                BoxFade(lambda t: t)
        elif event.unicode == u'+':
            IncrementSpotSize(+8)
        elif event.unicode == u'-':
            IncrementSpotSize(-8)
        elif event.unicode == u'[':
            SetGamma(new_gamma=Gamma / GammaStep)
        elif event.unicode == u']':
            SetGamma(new_gamma=Gamma * GammaStep)
        elif event.unicode == u'{':
            SetGamma(new_black=BlackLevel - BlackLevelStep)
        elif event.unicode == u'}':
            SetGamma(new_black=BlackLevel + BlackLevelStep)
        elif event.unicode == u'\\':
            SetGamma(1.0, 0)
        else:
            keyfunc = GetPageProp(Pcurrent, 'keys', {}).get(event.unicode, None)
            if keyfunc:
                SafeCall(keyfunc)
            elif IsValidShortcutKey(event.key):
                if event.mod & KMOD_SHIFT:
                    AssignShortcut(Pcurrent, event.key)
                else:
                    # load keyboard shortcut
                    page = FindShortcut(event.key)
                    if page and (page != Pcurrent):
                        TransitionTo(page)

    elif event.type == MOUSEBUTTONDOWN:
        if VideoPlaying:
            Marking = False
            Panning = False
            return
        MouseDownX, MouseDownY = event.pos
        if event.button == 1:
            MarkUL = MarkLR = MouseToScreen(event.pos)
        elif (event.button == 3) and ZoomMode:
            PanAnchorX = ZoomX0
            PanAnchorY = ZoomY0
        elif event.button == 4:
            IncrementSpotSize(+8)
        elif event.button == 5:
            IncrementSpotSize(-8)

    elif event.type == MOUSEBUTTONUP:
        if VideoPlaying:
            StopMPlayer()
            DrawCurrentPage()
            Marking = False
            Panning = False
            return
        if event.button == 2:
            LeaveZoomMode()
            DoOverview()
            return
        if event.button == 1:
            if Marking:
                # left mouse button released in marking mode -> stop box marking
                Marking = False
                # reject too small boxes
                if  (abs(MarkUL[0] - MarkLR[0]) > 0.04) \
                and (abs(MarkUL[1] - MarkLR[1]) > 0.03):
                    boxes = GetPageProp(Pcurrent, 'boxes', [])
                    oldboxcount = len(boxes)
                    boxes.append(NormalizeRect(MarkUL[0], MarkUL[1], MarkLR[0], MarkLR[1]))
                    SetPageProp(Pcurrent, 'boxes', boxes)
                    if not(oldboxcount) and not(Tracing):
                        BoxFade(lambda t: t)
                DrawCurrentPage()
            else:
                # left mouse button released, but no marking
                LeaveZoomMode()
                dest = GetNextPage(Pcurrent, 1)
                x, y = event.pos
                for valid, target, x0, y0, x1, y1 in GetPageProp(Pcurrent, '_href', []):
                    if valid and (x >= x0) and (x < x1) and (y >= y0) and (y < y1):
                        dest = target
                        break
                if type(dest) == types.IntType:
		    if PageClicks:
                        TransitionTo(dest)
                else:
                    RunURL(dest)
        if (event.button == 3) and not(Panning):
            # right mouse button -> check if a box has to be killed
            boxes = GetPageProp(Pcurrent, 'boxes', [])
            x, y = MouseToScreen(event.pos)
            try:
                # if a box is already present around the clicked position, kill it
                idx = FindBox(x, y, boxes)
                if (len(boxes) == 1) and not(Tracing):
                    BoxFade(lambda t: 1.0 - t)
                del boxes[idx]
                SetPageProp(Pcurrent, 'boxes', boxes)
                DrawCurrentPage()
            except ValueError:
                # no box present -> go to previous page
                if PageClicks and not ZoomMode:
                    TransitionTo(GetNextPage(Pcurrent, -1))
        Panning = False

    elif event.type == MOUSEMOTION:
        pygame.event.clear(MOUSEMOTION)
        # mouse move in fullscreen mode -> show mouse cursor and reset mouse timer
        if Fullscreen:
            pygame.time.set_timer(USEREVENT_HIDE_MOUSE, MouseHideDelay)
            SetCursor(True)
        # don't react on mouse input during video playback
        if VideoPlaying: return
        # activate marking if mouse is moved away far enough
        if event.buttons[0] and not(Marking):
            x, y = event.pos
            if (abs(x - MouseDownX) > 4) and (abs(y - MouseDownY) > 4):
                Marking = True
        # mouse move while marking -> update marking box
        if Marking:
            MarkLR = MouseToScreen(event.pos)
        # mouse move while RMB is pressed -> panning
        if event.buttons[2] and ZoomMode:
            x, y = event.pos
            if not(Panning) and (abs(x - MouseDownX) > 4) and (abs(y - MouseDownY) > 4):
                Panning = True
            ZoomX0 = PanAnchorX + (MouseDownX - x) * ZoomArea / ScreenWidth
            ZoomY0 = PanAnchorY + (MouseDownY - y) * ZoomArea / ScreenHeight
            ZoomX0 = min(max(ZoomX0, 0.0), 1.0 - ZoomArea)
            ZoomY0 = min(max(ZoomY0, 0.0), 1.0 - ZoomArea)
        # if anything changed, redraw the page
        if Marking or Tracing or event.buttons[2] or (CursorImage and CursorVisible):
            DrawCurrentPage()

    elif event.type == USEREVENT_HIDE_MOUSE:
        # mouse timer event -> hide fullscreen cursor
        pygame.time.set_timer(USEREVENT_HIDE_MOUSE, 0)
        SetCursor(False)
        DrawCurrentPage()

    elif event.type == USEREVENT_PAGE_TIMEOUT:
        TransitionTo(GetNextPage(Pcurrent, 1))

    elif event.type == USEREVENT_POLL_FILE:
        dirty = False
        for f in FileProps:
            s = my_stat(f)
            if s != GetFileProp(f, 'stat'):
                dirty = True
                SetFileProp(f, 'stat', s)
        if dirty:
            # first, check if the new file is valid
            if not os.path.isfile(GetPageProp(Pcurrent, '_file')):
                return
            # invalidate everything we used to know about the input files
            InvalidateCache()
            for props in PageProps.itervalues():
                for prop in ('_overview_rendered', '_box', '_href'):
                    if prop in props: del props[prop]
            LoadInfoScript()
            # force a transition to the current page, reloading it
            Pnext=-1
            TransitionTo(Pcurrent)
            # restart the background renderer thread. this is not completely safe,
            # i.e. there's a small chance that we fail to restart the thread, but
            # this isn't critical
            if CacheMode and BackgroundRendering:
                if RTrunning:
                    RTrestart = True
                else:
                    RTrunning = True
                    thread.start_new_thread(RenderThread, (Pcurrent, Pnext))

    elif event.type == USEREVENT_TIMER_UPDATE:
        if VideoPlaying and MPlayerProcess:
            if MPlayerProcess.poll() is not None:
                StopMPlayer()
                DrawCurrentPage()
        elif TimerTick():
            DrawCurrentPage()
