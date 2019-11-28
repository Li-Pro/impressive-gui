##### EVENT HANDLING ###########################################################

# set fullscreen mode
def SetFullscreen(fs, do_init=True):
    global Fullscreen
    if FakeFullscreen:
        return  # this doesn't work in fake-fullscreen mode
    if do_init:
        if fs == Fullscreen: return
        if not Platform.ToggleFullscreen(): return
    Fullscreen = fs
    DrawCurrentPage()
    if fs:
        Platform.ScheduleEvent("$hide-mouse", MouseHideDelay)
    else:
        Platform.ScheduleEvent("$hide-mouse", 0)
        SetCursor(True)

# PageProp toggle
def TogglePageProp(prop, default):
    global WantStatus
    SetPageProp(Pcurrent, prop, not(GetPageProp(Pcurrent, prop, default)))
    UpdateCaption(Pcurrent, force=True)
    WantStatus = True
    DrawCurrentPage()

# basic action implementations (i.e. stuff that is required to work, except in overview mode)
class BaseDisplayActions(BaseActions):
    def _X_quit(self):
        if FadeInOut:
            EnterFadeMode()
        PageLeft()
        Quit()

    def _X_expose(self):
        DrawCurrentPage()

    def _X_hide_mouse(self):
        # mouse timer event -> hide fullscreen cursor
        SetCursor(False)
        DrawCurrentPage()

    def _X_page_timeout(self):
        global NextPageAfterVideo
        if VideoPlaying:
            NextPageAfterVideo = True
        else:
            TransitionTo(GetNextPage(Pcurrent, 1))

    def _X_poll_file(self):
        global RTrunning, RTrestart, Pnext
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
            for props in PageProps.values():
                for prop in ('_overview_rendered', '_box', '_href'):
                    if prop in props: del props[prop]
            LoadInfoScript()
            # force a transition to the current page, reloading it
            Pnext = -1
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

    def _X_timer_update(self):
        if VideoPlaying and MPlayerProcess:
            if MPlayerProcess.poll() is not None:
                StopMPlayer()
                DrawCurrentPage()
        elif TimerTick():
            DrawCurrentPage()

# action implementations for video playback
class VideoActions(BaseDisplayActions):
    def _video_stop(self):
        "stop video playback"
        StopMPlayer()
        DrawCurrentPage()

    def player_command(self, mplayer_cmd, omxplayer_cmd):
        "helper for the various video-* actions"
        cmd = omxplayer_cmd if Platform.use_omxplayer else (mplayer_cmd + '\n')
        if not cmd: return
        try:
            MPlayerProcess.stdin.write(cmd)
            MPlayerProcess.stdin.flush()
        except:
            StopMPlayer()
            DrawCurrentPage()
    def _video_pause(self):
        "pause video playback"
        self.player_command("pause", 'p')
    def _video_step(self):
        "advance to the next frame in paused video"
        self.player_command("framestep", None)
    def _video_seek_backward_10(self):
        "seek 10 seconds backward in video"
        self.player_command("seek -10 pausing_keep", '\x1b[D')
    def _video_seek_backward_1(self):
        "seek 1 second backward in video"
        self.player_command("seek -1 pausing_keep", None)
    def _video_seek_forward_1(self):
        "seek 1 second forward in video"
        self.player_command("seek 1 pausing_keep", None)
    def _video_seek_forward_10(self):
        "seek 10 seconds forward in video"
        self.player_command("seek 10 pausing_keep", '\x1b[C')
VideoActions = VideoActions()

# action implementation for normal page display (i.e. everything except overview mode)
class PageDisplayActions(BaseDisplayActions):
    def _X_move(self):
        global Marking, MarkLR, Panning, ZoomX0, ZoomY0
        BaseActions._X_move(self)
        x, y = Platform.GetMousePos()
        # activate marking if mouse is moved away far enough
        if MarkValid and not(Marking):
            if (abs(x - MarkBaseX) > 4) and (abs(y - MarkBaseY) > 4):
                Marking = True
        # mouse move while marking -> update marking box
        if Marking:
            MarkLR = MouseToScreen((x, y))
        # mouse move while RMB is pressed -> panning
        if PanValid and ZoomMode:
            if not(Panning) and (abs(x - PanBaseX) > 1) and (abs(y - PanBaseY) > 1):
                Panning = True
            # ZoomArea is guaranteed to be float
            ZoomX0 = PanAnchorX + (PanBaseX - x) * ZoomArea / ScreenWidth
            ZoomY0 = PanAnchorY + (PanBaseY - y) * ZoomArea / ScreenHeight
            ZoomX0 = min(max(ZoomX0, 0.0), 1.0 - ZoomArea)
            ZoomY0 = min(max(ZoomY0, 0.0), 1.0 - ZoomArea)
        # if anything changed, redraw the page
        if Marking or Tracing or Panning or (CursorImage and CursorVisible):
            DrawCurrentPage()

    def _zoom_pan_ACTIVATE(self):
        "pan visible region in zoom mode"
        global PanValid, Panning, PanBaseX, PanBaseY, PanAnchorX, PanAnchorY
        ActionValidIf(ZoomMode and not(BoxZoom))
        PanValid = True
        Panning = False
        PanBaseX, PanBaseY = Platform.GetMousePos()
        PanAnchorX = ZoomX0
        PanAnchorY = ZoomY0
    def _zoom_pan(self):
        ActionValidIf(ZoomMode and Panning)
    def _zoom_pan_RELEASE(self):
        global PanValid, Panning
        PanValid = False
        Panning = False

    def _zoom_enter(self):
        "enter zoom mode"
        ActionValidIf(not(ZoomMode))
        tx, ty = MouseToScreen(Platform.GetMousePos())
        EnterZoomMode(DefaultZoomFactor,
                      (1.0 - 1.0 / DefaultZoomFactor) * tx,
                      (1.0 - 1.0 / DefaultZoomFactor) * ty)
    def _zoom_exit(self):
        "leave zoom mode"
        ActionValidIf(ZoomMode)
        LeaveZoomMode()

    def _box_add_ACTIVATE(self):
        "draw a new highlight box [mouse-only]"
        global MarkValid, Marking, MarkBaseX, MarkBaseY, MarkUL, MarkLR
        MarkValid = True
        Marking = False
        MarkBaseX, MarkBaseY = Platform.GetMousePos()
        MarkUL = MarkLR = MouseToScreen((MarkBaseX, MarkBaseY))
    def _box_add(self):
        global Marking
        ActionValidIf(Marking)
        Marking = False
        if BoxTooSmall():
            raise ActionNotHandled()
        boxes = GetPageProp(Pcurrent, 'boxes', [])
        oldboxcount = len(boxes)
        boxes.append(NormalizeRect(MarkUL[0], MarkUL[1], MarkLR[0], MarkLR[1]))
        SetPageProp(Pcurrent, 'boxes', boxes)
        if not(oldboxcount) and not(Tracing):
            BoxFade(lambda t: t)
        DrawCurrentPage()
    def _box_add_RELEASE(self):
        global MarkValid
        MarkValid = False

    def _box_remove(self):
        "remove the highlight box under the mouse cursor"
        ActionValidIf(not(Panning) and not(Marking))
        boxes = GetPageProp(Pcurrent, 'boxes', [])
        x, y = MouseToScreen(Platform.GetMousePos())
        try:
            # if a box is already present around the clicked position, kill it
            idx = FindBox(x, y, boxes)
            if (len(boxes) == 1) and not(Tracing):
                BoxFade(lambda t: 1.0 - t)
            del boxes[idx]
            SetPageProp(Pcurrent, 'boxes', boxes)
            DrawCurrentPage()
        except ValueError:
            # no box present
            raise ActionNotHandled()

    def _box_clear(self):
        "remove all highlight boxes on the current page"
        ActionValidIf(GetPageProp(Pcurrent, 'boxes'))
        if not Tracing:
            BoxFade(lambda t: 1.0 - t)
        DelPageProp(Pcurrent, 'boxes')
        DrawCurrentPage()

    def _box_zoom_ACTIVATE(self):
        "draw a box to zoom into [mouse-only]"
        ActionValidIf(not(BoxZoom) and not(Tracing) and not(GetPageProp(Pcurrent, 'boxes')))
        return self._box_add_ACTIVATE()
    def _box_zoom(self):
        global Marking, BoxZoom, ZoomBox
        ActionValidIf(Marking and not(BoxZoom) and not(Tracing) and not(GetPageProp(Pcurrent, 'boxes')))
        Marking = False
        if BoxTooSmall():
            raise ActionNotHandled()
        zxRatio = 0.5 if HalfScreen else 1.0
        z = min(zxRatio / abs(MarkUL[0] - MarkLR[0]), 1.0 / abs(MarkUL[1] - MarkLR[1]))
        if z <= 1:
            return DrawCurrentPage()
        if HalfScreen:
            tx = MarkLR[0]
        else:
            tx = (MarkUL[0] + MarkLR[0]) * 0.5
        ty = (MarkUL[1] + MarkLR[1]) * 0.5
        tx = tx + (tx - 0.5) / (z - 1.0)
        ty = ty + (ty - 0.5) / (z - 1.0)
        tx = (1.0 - 1.0 / z) * tx
        ty = (1.0 - 1.0 / z) * ty
        BoxZoom = NormalizeRect(MarkUL[0], MarkUL[1], MarkLR[0], MarkLR[1])
        EnterZoomMode(z, tx, ty)
    def _box_zoom_RELEASE(self):
        return self._box_add_RELEASE()

    def _box_zoom_exit(self):
        "leave box-zoom mode"
        ActionValidIf(BoxZoom)
        LeaveZoomMode()

    def _hyperlink(self, allow_transition=True):
        "navigate to the hyperlink under the mouse cursor"
        x, y = Platform.GetMousePos()
        for valid, target, x0, y0, x1, y1 in GetPageProp(Pcurrent, '_href', []):
            if valid and (x >= x0) and (x < x1) and (y >= y0) and (y < y1):
                if isinstance(target, int):
                    TransitionTo(target, allow_transition=allow_transition)
                elif target:
                    RunURL(target)
                return
        raise ActionNotHandled()
    def _hyperlink_notrans(self):
        "like 'hyperlink', but no transition on page change"
        return self._hyperlink(allow_transition=False)

    def _goto_prev(self):
        "go to the previous page (with transition)"
        TransitionTo(GetNextPage(Pcurrent, -1), allow_transition=True)
    def _goto_prev_notrans(self):
        "go to the previous page (without transition)"
        TransitionTo(GetNextPage(Pcurrent, -1), allow_transition=False)
    def _goto_next(self):
        "go to the next page (with transition)"
        TransitionTo(GetNextPage(Pcurrent, +1), allow_transition=True)
    def _goto_next_notrans(self):
        "go to the next page (without transition)"
        TransitionTo(GetNextPage(Pcurrent, +1), allow_transition=False)
    def _goto_last(self):
        "go to the last visited page (with transition)"
        TransitionTo(LastPage, allow_transition=True)
    def _goto_last_notrans(self):
        "go to the last visited page (without transition)"
        TransitionTo(LastPage, allow_transition=False)
    def _goto_start(self):
        "go to the first page (with transition)"
        ActionValidIf(Pcurrent != 1)
        TransitionTo(1, allow_transition=True)
    def _goto_start_notrans(self):
        "go to the first page (without transition)"
        ActionValidIf(Pcurrent != 1)
        TransitionTo(1, allow_transition=False)
    def _goto_end(self):
        "go to the final page (with transition)"
        ActionValidIf(Pcurrent != PageCount)
        TransitionTo(PageCount, allow_transition=True)
    def _goto_end_notrans(self):
        "go to the final page (without transition)"
        ActionValidIf(Pcurrent != PageCount)
        TransitionTo(PageCount, allow_transition=False)

    def _overview_enter(self):
        "zoom out to the overview page"
        if not EnableOverview: return
        LeaveZoomMode()
        DoOverview()

    def _spotlight_enter(self):
        "enter spotlight mode"
        global Tracing
        ActionValidIf(not(Tracing))
        Tracing = True
        if GetPageProp(Pcurrent, 'boxes'):
            DrawCurrentPage()
        else:
            BoxFade(lambda t: t)
    def _spotlight_exit(self):
        "exit spotlight mode"
        global Tracing
        ActionValidIf(Tracing)
        if not GetPageProp(Pcurrent, 'boxes'):
            BoxFade(lambda t: 1.0 - t)
        Tracing = False
        DrawCurrentPage()

    def _spotlight_shrink(self):
        "decrease the spotlight radius"
        ActionValidIf(Tracing)
        IncrementSpotSize(-8)
    def _spotlight_grow(self):
        "increase the spotlight radius"
        ActionValidIf(Tracing)
        IncrementSpotSize(+8)
    def _spotlight_reset(self):
        "reset the spotlight radius to its default value"
        global SpotRadius
        ActionValidIf(Tracing)
        SpotRadius = SpotRadiusBase
        GenerateSpotMesh()
        DrawCurrentPage()

    def _zoom_in(self):
        "zoom in a small bit"
        ActionValidIf((MouseWheelZoom or ZoomMode) and not(BoxZoom))
        ChangeZoom(ViewZoomFactor * ZoomStep, Platform.GetMousePos())
    def _zoom_out(self):
        "zoom out a small bit"
        ActionValidIf((MouseWheelZoom or ZoomMode) and not(BoxZoom))
        # ZoomStep is guaranteed to be float
        ChangeZoom(ViewZoomFactor / ZoomStep, Platform.GetMousePos())

    def _zoom_update(self):
        "re-render the page in the current zoom resolution"
        ActionValidIf(ZoomMode)
        ReRenderZoom(ViewZoomFactor)

    def _fullscreen(self):
        "toggle fullscreen mode"
        SetFullscreen(not(Fullscreen))

    def _save(self):
        "save the info script"
        SaveInfoScript(InfoScriptPath)

    def _fade_to_black(self):
        "fade to a black screen"
        FadeMode(0.0)
    def _fade_to_white(self):
        "fade to a white screen"
        FadeMode(1.0)

    def _auto_stop(self):
        "stop automatic slideshow"
        global AutoAdvanceEnabled, PageTimeout
        AutoAdvanceEnabled = False
        PageTimeout = 0
        Platform.ScheduleEvent('$page-timeout', 0)
        if AutoAdvanceProgress:
            DrawCurrentPage()
    def _auto_start(self):
        "start or resume automatic slideshow"
        global AutoAdvanceEnabled, PageTimeout
        AutoAdvanceEnabled = True
        PageTimeout = AutoAdvanceTime
        if (GetPageProp(Pcurrent, '_shown') == 1) or Wrap:
            PageTimeout = GetPageProp(Pcurrent, 'timeout', PageTimeout)
        dt = PageTimeout - (Platform.GetTicks() - PageEnterTime)
        if dt > 0:
            Platform.ScheduleEvent('$page-timeout', dt)
        else:
            TransitionTo(GetNextPage(Pcurrent, 1))
    def _auto_toggle(self):
        "toggle automatic slideshow"
        if AutoAdvanceEnabled:
            self._auto_stop()
        else:
            self._auto_start()

    def _time_toggle(self):
        "toggle time display and/or time tracking mode"
        global TimeDisplay
        TimeDisplay = not(TimeDisplay)
        DrawCurrentPage()
        EnableTimeTracking()
    def _time_reset(self):
        "reset the on-screen timer"
        ResetTimer()
        if TimeDisplay:
            DrawCurrentPage()

    def _toggle_skip(self):
        "toggle 'skip' flag of current page"
        TogglePageProp('skip', False)
    def _toggle_overview(self):
        "toggle 'visible on overview' flag of current page"
        TogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))

    def _fade_less(self):
        "decrease the spotlight/box background darkness"
        global BoxFadeDarkness, BoxZoomDarkness
        if BoxZoom:
            BoxZoomDarkness = max(0.0, BoxZoomDarkness - BoxFadeDarknessStep)
        else:
            BoxFadeDarkness = max(0.0, BoxFadeDarkness - BoxFadeDarknessStep)
        DrawCurrentPage()
    def _fade_more(self):
        "increase the spotlight/box background darkness"
        global BoxFadeDarkness, BoxZoomDarkness
        if BoxZoom:
            BoxZoomDarkness = min(1.0, BoxZoomDarkness + BoxFadeDarknessStep)
        else:
            BoxFadeDarkness = min(1.0, BoxFadeDarkness + BoxFadeDarknessStep)
        DrawCurrentPage()
    def _fade_reset(self):
        "reset spotlight/box background darkness to default"
        global BoxFadeDarkness, BoxZoomDarkness
        BoxFadeDarkness = BoxFadeDarknessBase
        BoxZoomDarkness = BoxZoomDarknessBase
        DrawCurrentPage()

    def _gamma_decrease(self):
        "decrease gamma"
        # GammaStep is guaranteed to be float
        SetGamma(new_gamma=Gamma / GammaStep)
    def _gamma_increase(self):
        "increase gamma"
        SetGamma(new_gamma=Gamma * GammaStep)
    def _gamma_bl_decrease(self):
        "decrease black level"
        SetGamma(new_black=BlackLevel - BlackLevelStep)
    def _gamma_bl_increase(self):
        "increase black level"
        SetGamma(new_black=BlackLevel + BlackLevelStep)
    def _gamma_reset(self):
        "reset gamma and black level to the defaults"
        SetGamma(1.0, 0)

PageDisplayActions = PageDisplayActions()
ForcedActions.update(("-zoom-pan", "+zoom-pan", "-box-add", "+box-add", "-box-zoom", "+box-zoom"))

# main event handling function
# takes care that $page-timeout events are handled with least priority
def EventHandlerLoop():
    poll = True
    page_timeout = False
    while True:
        ev = Platform.GetEvent(poll)
        poll = bool(ev)
        if not ev:
            # no more events in the queue -> can now insert a $page-timeout
            if page_timeout:
                ev = "$page-timeout"
                page_timeout = False
            else:
                continue
        elif ev == "$page-timeout":
            page_timeout = True
            continue

        if VideoPlaying:
            # video mode -> ignore all non-video actions
            ProcessEvent(ev, VideoActions)
        elif ProcessEvent(ev, PageDisplayActions):
            # normal action has been handled -> done
            pass
        elif ev and (ev[0] == '*'):
            keyfunc = GetPageProp(Pcurrent, 'keys', {}).get(ev[1:], None)
            if keyfunc:
                SafeCall(keyfunc)
            else:
                # handle a shortcut key
                ctrl = ev.startswith('*ctrl+')
                if ctrl:
                    ev = '*' + ev[6:]
                page = HandleShortcutKey(ev, Pcurrent)
                if page:
                    TransitionTo(page, allow_transition=not(ctrl))
