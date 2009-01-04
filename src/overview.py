##### OVERVIEW MODE ############################################################

def UpdateOverviewTexture():
    global OverviewNeedUpdate
    glBindTexture(TextureTarget, Tnext)
    Loverview.acquire()
    try:
        glTexImage2D(TextureTarget, 0, 3, TexWidth, TexHeight, 0, \
                     GL_RGB, GL_UNSIGNED_BYTE, OverviewImage.tostring())
    finally:
        Loverview.release()
    OverviewNeedUpdate = False

# draw the overview page
def DrawOverview():
    if VideoPlaying: return
    glClear(GL_COLOR_BUFFER_BIT)
    glDisable(GL_BLEND)
    glEnable(TextureTarget)
    glBindTexture(TextureTarget, Tnext)
    glColor3ub(192, 192, 192)
    DrawFullQuad()

    pos = OverviewPos(OverviewSelection)
    X0 = PixelX *  pos[0]
    Y0 = PixelY *  pos[1]
    X1 = PixelX * (pos[0] + OverviewCellX)
    Y1 = PixelY * (pos[1] + OverviewCellY)
    glColor3d(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    DrawPoint(X0, Y0)
    DrawPoint(X1, Y0)
    DrawPoint(X1, Y1)
    DrawPoint(X0, Y1)
    glEnd()

    DrawOSDEx(OSDTitlePos,  CurrentOSDCaption)
    DrawOSDEx(OSDPagePos,   CurrentOSDPage)
    DrawOSDEx(OSDStatusPos, CurrentOSDStatus)
    DrawOverlays()
    pygame.display.flip()

# overview zoom effect, time mapped through func
def OverviewZoom(func):
    global TransitionRunning
    pos = OverviewPos(OverviewSelection)
    X0 = PixelX * (pos[0] + OverviewBorder)
    Y0 = PixelY * (pos[1] + OverviewBorder)
    X1 = PixelX * (pos[0] - OverviewBorder + OverviewCellX)
    Y1 = PixelY * (pos[1] - OverviewBorder + OverviewCellY)

    TransitionRunning = True
    t0 = pygame.time.get_ticks()
    while not(VideoPlaying):
        t = (pygame.time.get_ticks() - t0) * 1.0 / ZoomDuration
        if t >= 1.0: break
        t = func(t)
        t1 = t*t
        t = 1.0 - t1

        zoom = (t * (X1 - X0) + t1) / (X1 - X0)
        OX = zoom * (t * X0 - X0) - (zoom - 1.0) * t * X0
        OY = zoom * (t * Y0 - Y0) - (zoom - 1.0) * t * Y0
        OX = t * X0 - zoom * X0
        OY = t * Y0 - zoom * Y0

        glDisable(GL_BLEND)
        glEnable(TextureTarget)
        glBindTexture(TextureTarget, Tnext)
        glBegin(GL_QUADS)
        glColor3ub(192, 192, 192)
        glTexCoord2d(    0.0,     0.0);  glVertex2d(OX,        OY)
        glTexCoord2d(TexMaxS,     0.0);  glVertex2d(OX + zoom, OY)
        glTexCoord2d(TexMaxS, TexMaxT);  glVertex2d(OX + zoom, OY + zoom)
        glTexCoord2d(    0.0, TexMaxT);  glVertex2d(OX,        OY + zoom)
        glColor3ub(255, 255, 255)
        glTexCoord2d(X0 * TexMaxS, Y0 * TexMaxT);  glVertex2d(OX + X0*zoom, OY + Y0 * zoom)
        glTexCoord2d(X1 * TexMaxS, Y0 * TexMaxT);  glVertex2d(OX + X1*zoom, OY + Y0 * zoom)
        glTexCoord2d(X1 * TexMaxS, Y1 * TexMaxT);  glVertex2d(OX + X1*zoom, OY + Y1 * zoom)
        glTexCoord2d(X0 * TexMaxS, Y1 * TexMaxT);  glVertex2d(OX + X0*zoom, OY + Y1 * zoom)
        glEnd()

        EnableAlphaBlend()
        glBindTexture(TextureTarget, Tcurrent)
        glColor4d(1.0, 1.0, 1.0, 1.0 - t * t * t)
        glBegin(GL_QUADS)
        glTexCoord2d(    0.0,     0.0);  glVertex2d(t * X0,      t * Y0)
        glTexCoord2d(TexMaxS,     0.0);  glVertex2d(t * X1 + t1, t * Y0)
        glTexCoord2d(TexMaxS, TexMaxT);  glVertex2d(t * X1 + t1, t * Y1 + t1)
        glTexCoord2d(    0.0, TexMaxT);  glVertex2d(t * X0,      t * Y1 + t1)
        glEnd()

        DrawOSDEx(OSDTitlePos,  CurrentOSDCaption, alpha_factor=t)
        DrawOSDEx(OSDPagePos,   CurrentOSDPage,    alpha_factor=t)
        DrawOSDEx(OSDStatusPos, CurrentOSDStatus,  alpha_factor=t)
        DrawOverlays()
        pygame.display.flip()
    TransitionRunning = False

# overview keyboard navigation
def OverviewKeyboardNav(delta):
    global OverviewSelection
    dest = OverviewSelection + delta
    if (dest >= OverviewPageCount) or (dest < 0):
        return
    OverviewSelection = dest
    x, y = OverviewPos(OverviewSelection)
    pygame.mouse.set_pos((x + (OverviewCellX / 2), y + (OverviewCellY / 2)))

# overview mode PageProp toggle
def OverviewTogglePageProp(prop, default):
    if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
        return
    page = OverviewPageMap[OverviewSelection]
    SetPageProp(page, prop, not(GetPageProp(page, prop, default)))
    UpdateCaption(page, force=True)
    DrawOverview()

# overview event handler
def HandleOverviewEvent(event):
    global OverviewSelection, TimeDisplay

    if event.type == QUIT:
        PageLeft(overview=True)
        Quit()
    elif event.type == VIDEOEXPOSE:
        DrawOverview()

    elif event.type == KEYDOWN:
        if (event.key == K_ESCAPE) or (event.unicode == u'q'):
            pygame.event.post(pygame.event.Event(QUIT))
        elif event.unicode == u'f':
            SetFullscreen(not Fullscreen)
        elif event.unicode == u't':
            TimeDisplay = not(TimeDisplay)
            DrawOverview()
        elif event.unicode == u'r':
            ResetTimer()
            if TimeDisplay: DrawOverview()
        elif event.unicode == u's':
            SaveInfoScript(InfoScriptPath)
        elif event.unicode == u'o':
            OverviewTogglePageProp('overview', GetPageProp(Pcurrent, '_overview', True))
        elif event.unicode == u'i':
            OverviewTogglePageProp('skip', False)
        elif event.key == K_UP:    OverviewKeyboardNav(-OverviewGridSize)
        elif event.key == K_LEFT:  OverviewKeyboardNav(-1)
        elif event.key == K_RIGHT: OverviewKeyboardNav(+1)
        elif event.key == K_DOWN:  OverviewKeyboardNav(+OverviewGridSize)
        elif event.key == K_TAB:
            OverviewSelection = -1
            return 0
        elif event.key in (K_RETURN, K_KP_ENTER):
            return 0
        elif IsValidShortcutKey(event.key):
            if event.mod & KMOD_SHIFT:
                try:
                    AssignShortcut(OverviewPageMap[OverviewSelection], event.key)
                except IndexError:
                    pass   # no valid page selected
            else:
                # load shortcut
                page = FindShortcut(event.key)
                if page:
                    OverviewSelection = OverviewPageMapInv[page]
                    x, y = OverviewPos(OverviewSelection)
                    pygame.mouse.set_pos((x + (OverviewCellX / 2), \
                                          y + (OverviewCellY / 2)))
                    DrawOverview()

    elif event.type == MOUSEBUTTONUP:
        if event.button == 1:
            return 0
        elif event.button in (2, 3):
            OverviewSelection = -1
            return 0

    elif event.type == MOUSEMOTION:
        pygame.event.clear(MOUSEMOTION)
        # mouse move in fullscreen mode -> show mouse cursor and reset mouse timer
        if Fullscreen:
            pygame.time.set_timer(USEREVENT_HIDE_MOUSE, MouseHideDelay)
            SetCursor(True)
        # determine highlighted page
        OverviewSelection = \
             int((event.pos[0] - OverviewOfsX) / OverviewCellX) + \
             int((event.pos[1] - OverviewOfsY) / OverviewCellY) * OverviewGridSize
        if (OverviewSelection < 0) or (OverviewSelection >= len(OverviewPageMap)):
            UpdateCaption(0)
        else:
            UpdateCaption(OverviewPageMap[OverviewSelection])
        DrawOverview()

    elif event.type == USEREVENT_HIDE_MOUSE:
        # mouse timer event -> hide fullscreen cursor
        pygame.time.set_timer(USEREVENT_HIDE_MOUSE, 0)
        SetCursor(False)
        DrawOverview()

    return 1

# overview mode entry/loop/exit function
def DoOverview():
    global Pcurrent, Pnext, Tcurrent, Tnext, Tracing, OverviewSelection
    global PageEnterTime, OverviewMode

    pygame.time.set_timer(USEREVENT_PAGE_TIMEOUT, 0)
    PageLeft()
    UpdateOverviewTexture()

    if GetPageProp(Pcurrent, 'boxes') or Tracing:
        BoxFade(lambda t: 1.0 - t)
    Tracing = False
    OverviewSelection = OverviewPageMapInv[Pcurrent]

    OverviewMode = True
    OverviewZoom(lambda t: 1.0 - t)
    DrawOverview()
    PageEnterTime = pygame.time.get_ticks() - StartTime
    while True:
        event = pygame.event.poll()
        if event.type == NOEVENT:
            force_update = OverviewNeedUpdate
            if OverviewNeedUpdate:
                UpdateOverviewTexture()
            if TimerTick() or force_update:
                DrawOverview()
            pygame.time.wait(20)
        elif not HandleOverviewEvent(event):
            break
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
