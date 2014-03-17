##### OVERVIEW MODE ############################################################

def UpdateOverviewTexture():
    global OverviewNeedUpdate
    Loverview.acquire()
    try:
        gl.load_texture(gl.TEXTURE_2D, Tnext, OverviewImage)
    finally:
        Loverview.release()
    OverviewNeedUpdate = False

# draw the overview page
def DrawOverview():
    if VideoPlaying: return
    gl.Clear(gl.COLOR_BUFFER_BIT)
    TexturedRectShader.get_instance().draw(
        0.0, 0.0, 1.0, 1.0,
        s1=TexMaxS, t1=TexMaxT,
        tex=Tnext, color=0.75
    )

    pos = OverviewPos(OverviewSelection)
    X0 = PixelX *  pos[0]
    Y0 = PixelY *  pos[1]
    X1 = PixelX * (pos[0] + OverviewCellX)
    Y1 = PixelY * (pos[1] + OverviewCellY)
    TexturedRectShader.get_instance().draw(
        X0, Y0, X1, Y1,
        X0 * TexMaxS, Y0 * TexMaxT,
        X1 * TexMaxS, Y1 * TexMaxT,
        color=1.0
    )

    gl.Enable(gl.BLEND)
    OSDFont.BeginDraw()
    DrawOSDEx(OSDTitlePos,  CurrentOSDCaption)
    DrawOSDEx(OSDPagePos,   CurrentOSDPage)
    DrawOSDEx(OSDStatusPos, CurrentOSDStatus)
    OSDFont.EndDraw()
    DrawOverlays()
    Platform.SwapBuffers()

# overview zoom effect, time mapped through func
def OverviewZoom(func):
    global TransitionRunning
    if ZoomDuration <= 0:
        return
    pos = OverviewPos(OverviewSelection)
    X0 = PixelX * (pos[0] + OverviewBorder)
    Y0 = PixelY * (pos[1] + OverviewBorder)
    X1 = PixelX * (pos[0] - OverviewBorder + OverviewCellX)
    Y1 = PixelY * (pos[1] - OverviewBorder + OverviewCellY)

    shader = TexturedRectShader.get_instance()
    TransitionRunning = True
    t0 = Platform.GetTicks()
    while not(VideoPlaying):
        t = (Platform.GetTicks() - t0) * 1.0 / ZoomDuration
        if t >= 1.0: break
        t = func(t)
        t1 = t*t
        t = 1.0 - t1

        zoom = (t * (X1 - X0) + t1) / (X1 - X0)
        OX = zoom * (t * X0 - X0) - (zoom - 1.0) * t * X0
        OY = zoom * (t * Y0 - Y0) - (zoom - 1.0) * t * Y0
        OX = t * X0 - zoom * X0
        OY = t * Y0 - zoom * Y0

        gl.Clear(gl.COLOR_BUFFER_BIT)
        shader.draw(  # base overview page
            OX, OY, OX + zoom, OY + zoom,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tnext, color=0.75
        )
        shader.draw(  # highlighted part
            OX + X0 * zoom, OY + Y0 * zoom,
            OX + X1 * zoom, OY + Y1 * zoom,
            X0 * TexMaxS, Y0 * TexMaxT,
            X1 * TexMaxS, Y1 * TexMaxT,
            color=1.0
        )
        gl.Enable(gl.BLEND)
        shader.draw(  # overlay of the original high-res page
            t * X0,      t * Y0,
            t * X1 + t1, t * Y1 + t1,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tcurrent, color=(1.0, 1.0, 1.0, 1.0 - t * t * t)
        )

        OSDFont.BeginDraw()
        DrawOSDEx(OSDTitlePos,  CurrentOSDCaption, alpha_factor=t)
        DrawOSDEx(OSDPagePos,   CurrentOSDPage,    alpha_factor=t)
        DrawOSDEx(OSDStatusPos, CurrentOSDStatus,  alpha_factor=t)
        OSDFont.EndDraw()
        DrawOverlays()
        Platform.SwapBuffers()
    TransitionRunning = False

# overview keyboard navigation
def OverviewKeyboardNav(delta):
    global OverviewSelection
    dest = OverviewSelection + delta
    if (dest >= OverviewPageCount) or (dest < 0):
        return
    OverviewSelection = dest
    x, y = OverviewPos(OverviewSelection)
    Platform.SetMousePos((x + (OverviewCellX / 2), y + (OverviewCellY / 2)))

# overview mode PageProp toggle
def OverviewTogglePageProp(prop, default):
    if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
        return
    page = OverviewPageMap[OverviewSelection]
    SetPageProp(page, prop, not(GetPageProp(page, prop, default)))
    UpdateCaption(page, force=True)
    DrawOverview()

class ExitOverview(Exception):
    pass

# action implementation for overview mode
class OverviewActions(BaseActions):
    def _X_move(self):
        global OverviewSelection
        BaseActions._X_move(self)
        # determine highlighted page
        x, y = Platform.GetMousePos()
        OverviewSelection = \
             int((x - OverviewOfsX) / OverviewCellX) + \
             int((y - OverviewOfsY) / OverviewCellY) * OverviewGridSize
        if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
            UpdateCaption(0)
        else:
            UpdateCaption(OverviewPageMap[OverviewSelection])
        DrawOverview()

    def _X_quit(self):
        PageLeft(overview=True)
        Quit()

    def _X_expose(self):
        DrawOverview()

    def _X_hide_mouse(self):
        # mouse timer event -> hide fullscreen cursor
        SetCursor(False)
        DrawOverview()

    def _X_timer_update(self):
        force_update = OverviewNeedUpdate
        if OverviewNeedUpdate:
            UpdateOverviewTexture()
        if TimerTick() or force_update:
            DrawOverview()

    def _overview_exit(self):
        "exit overview mode and return to the last page"
        global OverviewSelection
        OverviewSelection = -1
        raise ExitOverview
    def _overview_confirm(self):
        "exit overview mode and go to the selected page"
        raise ExitOverview

    def _fullscreen(self):
        SetFullscreen(not(Fullscreen))

    def _save(self):
        SaveInfoScript(InfoScriptPath)

    def _fade_to_black(self):
        FadeMode(0.0)
    def _fade_to_white(self):
        FadeMode(1.0)

    def _time_toggle(self):
        global TimeDisplay
        TimeDisplay = not(TimeDisplay)
        DrawOverview()
    def _time_reset(self):
        ResetTimer()
        if TimeDisplay:
            DrawOverview()

    def _toggle_skip(self):
        TogglePageProp('skip', False)
    def _toggle_overview(self):
        TogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))

    def _overview_up(self):
        "move the overview selection upwards"
        OverviewKeyboardNav(-OverviewGridSize)
    def _overview_prev(self):
        "select the previous page in overview mode"
        OverviewKeyboardNav(-1)
    def _overview_next(self):
        "select the next page in overview mode"
        OverviewKeyboardNav(+1)
    def _overview_down(self):
        "move the overview selection downwards"
        OverviewKeyboardNav(+OverviewGridSize)
OverviewActions = OverviewActions()

# overview mode entry/loop/exit function
def DoOverview():
    global Pcurrent, Pnext, Tcurrent, Tnext, Tracing, OverviewSelection
    global PageEnterTime, OverviewMode

    Platform.ScheduleEvent("$page-timeout", 0)
    PageLeft()
    UpdateOverviewTexture()

    if GetPageProp(Pcurrent, 'boxes') or Tracing:
        BoxFade(lambda t: 1.0 - t)
    Tracing = False
    OverviewSelection = OverviewPageMapInv[Pcurrent]

    OverviewMode = True
    OverviewZoom(lambda t: 1.0 - t)
    DrawOverview()
    PageEnterTime = Platform.GetTicks() - StartTime

    try:
        while True:
            ev = Platform.GetEvent()
            if not ev:
                continue
            if not ProcessEvent(ev, OverviewActions):
                try:
                    page = OverviewPageMap[OverviewSelection]
                except IndexError:
                    page = 0
                page = HandleShortcutKey(ev, page)
                if page:
                    OverviewSelection = OverviewPageMapInv[page]
                    x, y = OverviewPos(OverviewSelection)
                    Platform.SetMousePos((x + (OverviewCellX / 2), \
                                          y + (OverviewCellY / 2)))
                    DrawOverview()
    except ExitOverview:
        PageLeft(overview=True)

    if (OverviewSelection < 0) or (OverviewSelection >= OverviewPageCount):
        OverviewSelection = OverviewPageMapInv[Pcurrent]
        Pnext = Pcurrent
    else:
        Pnext = OverviewPageMap[OverviewSelection]
    if Pnext != Pcurrent:
        Pcurrent = Pnext
        RenderPage(Pcurrent, Tcurrent)
    UpdateCaption(Pcurrent)
    OverviewZoom(lambda t: t)
    OverviewMode = False
    DrawCurrentPage()

    if GetPageProp(Pcurrent, 'boxes'):
        BoxFade(lambda t: t)
    PageEntered()
    if not PreloadNextPage(GetNextPage(Pcurrent, 1)):
        PreloadNextPage(GetNextPage(Pcurrent, -1))
