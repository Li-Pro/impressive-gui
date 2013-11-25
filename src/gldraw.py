##### OPENGL RENDERING #########################################################

# draw OSD overlays
def DrawOverlays(trans_time=0.0):
    reltime = pygame.time.get_ticks() - StartTime
    if (EstimatedDuration or PageProgress or (PageTimeout and AutoAdvanceProgress)) \
    and (OverviewMode or GetPageProp(Pcurrent, 'progress', True)):
        r, g, b = ProgressBarColorPage
        a = ProgressBarAlpha
        if PageTimeout and AutoAdvanceProgress:
            rel = (reltime - PageEnterTime) / float(PageTimeout)
            if TransitionRunning:
                a = int(a * (1.0 - TransitionPhase))
            elif PageLeaveTime > PageEnterTime:
                # we'll be called one frame after the transition finished, but
                # before the new page has been fully activated => don't flash
                a = 0
        elif EstimatedDuration:
            rel = (0.001 * reltime) / EstimatedDuration
            if rel < 1.0:
                r, g, b = ProgressBarColorNormal
            elif rel < ProgressBarWarningFactor:
                r, g, b = lerpColor(ProgressBarColorNormal, ProgressBarColorWarning,
                          (rel - 1.0) / (ProgressBarWarningFactor - 1.0))
            elif rel < ProgressBarCriticalFactor:
                r, g, b = lerpColor(ProgressBarColorWarning, ProgressBarColorCritical,
                          (rel - ProgressBarWarningFactor) / (ProgressBarCriticalFactor - ProgressBarWarningFactor))
            else:
                r, g, b = ProgressBarColorCritical
        else:  # must be PageProgress
            rel = (Pcurrent + trans_time * (Pnext - Pcurrent)) / PageCount
        if HalfScreen:
            zero = 0.5
            rel = 0.5 + 0.5 * rel
        else:
            zero = 0.0
        glDisable(TextureTarget)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_QUADS)
        glColor4ub(r, g, b, 0)
        glVertex2d(zero, 1.0 - ProgressBarSizeFactor)
        glVertex2d(rel, 1.0 - ProgressBarSizeFactor)
        glColor4ub(r, g, b, a)
        glVertex2d(rel, 1.0)
        glVertex2d(zero, 1.0)
        glEnd()
        glDisable(GL_BLEND)
    if WantStatus:
        DrawOSDEx(OSDStatusPos, CurrentOSDStatus)
    if TimeDisplay:
        if ShowClock:
            DrawOSDEx(OSDTimePos, ClockTime(MinutesOnly))
        else:
            t = reltime / 1000
            DrawOSDEx(OSDTimePos, FormatTime(t, MinutesOnly))
    if CurrentOSDComment and (OverviewMode or not(TransitionRunning)):
        DrawOSD(ScreenWidth/2, \
                ScreenHeight - 3*OSDMargin - FontSize, \
                CurrentOSDComment, Center, Up)
    if CursorImage and CursorVisible:
        x, y = pygame.mouse.get_pos()
        x -= CursorHotspot[0]
        y -= CursorHotspot[1]
        X0 = x * PixelX
        Y0 = y * PixelY
        X1 = X0 + CursorSX
        Y1 = Y0 + CursorSY
        glDisable(TextureTarget)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, CursorTexture)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4ub(255, 255, 255, 255)
        glBegin(GL_QUADS)
        glTexCoord2d(0.0,      0.0);       glVertex2d(X0, Y0)
        glTexCoord2d(CursorTX, 0.0);       glVertex2d(X1, Y0)
        glTexCoord2d(CursorTX, CursorTY);  glVertex2d(X1, Y1)
        glTexCoord2d(0.0,      CursorTY);  glVertex2d(X0, Y1)
        glEnd()
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

# draw the complete image of the current page
def DrawCurrentPage(dark=1.0, do_flip=True):
    if VideoPlaying: return
    boxes = GetPageProp(Pcurrent, 'boxes')
    glClear(GL_COLOR_BUFFER_BIT)

    # pre-transform for zoom
    glLoadIdentity()
    glOrtho(ZoomX0, ZoomX0 + ZoomArea,  ZoomY0 + ZoomArea, ZoomY0,  -10.0, 10.0)

    # background layer -- the page's image, darkened if it has boxes
    glDisable(GL_BLEND)
    glEnable(TextureTarget)
    glBindTexture(TextureTarget, Tcurrent)
    if boxes or Tracing:
        light = 1.0 - BoxFadeDarkness * dark
    else:
        light = 1.0
    glColor3d(light, light, light)
    DrawFullQuad()

    if boxes or Tracing:
        # alpha-blend the same image some times to blur it
        EnableAlphaBlend()
        DrawTranslatedFullQuad(+PixelX * ZoomArea, 0.0, light, dark / 2)
        DrawTranslatedFullQuad(-PixelX * ZoomArea, 0.0, light, dark / 3)
        DrawTranslatedFullQuad(0.0, +PixelY * ZoomArea, light, dark / 4)
        DrawTranslatedFullQuad(0.0, -PixelY * ZoomArea, light, dark / 5)

    if boxes:
        # draw outer box fade
        EnableAlphaBlend()
        for X0, Y0, X1, Y1 in boxes:
            glBegin(GL_QUAD_STRIP)
            DrawPointEx(X0, Y0, 1);  DrawPointEx(X0 - EdgeX, Y0 - EdgeY, 0)
            DrawPointEx(X1, Y0, 1);  DrawPointEx(X1 + EdgeX, Y0 - EdgeY, 0)
            DrawPointEx(X1, Y1, 1);  DrawPointEx(X1 + EdgeX, Y1 + EdgeY, 0)
            DrawPointEx(X0, Y1, 1);  DrawPointEx(X0 - EdgeX, Y1 + EdgeY, 0)
            DrawPointEx(X0, Y0, 1);  DrawPointEx(X0 - EdgeX, Y0 - EdgeY, 0)
            glEnd()

        # draw boxes
        glDisable(GL_BLEND)
        glBegin(GL_QUADS)
        for X0, Y0, X1, Y1 in boxes:
            DrawPoint(X0, Y0)
            DrawPoint(X1, Y0)
            DrawPoint(X1, Y1)
            DrawPoint(X0, Y1)
        glEnd()

    if Tracing:
        x, y = MouseToScreen(pygame.mouse.get_pos())
        # outer spot fade
        EnableAlphaBlend()
        glBegin(GL_TRIANGLE_STRIP)
        for x0, y0, x1, y1 in SpotMesh:
            DrawPointEx(x + x0, y + y0, 1)
            DrawPointEx(x + x1, y + y1, 0)
        glEnd()
        # inner spot
        glDisable(GL_BLEND)
        glBegin(GL_TRIANGLE_FAN)
        DrawPoint(x, y)
        for x0, y0, x1, y1 in SpotMesh:
            DrawPoint(x + x0, y + y0)
        glEnd()

    if Marking:
        # soft alpha-blended rectangle
        glDisable(TextureTarget)
        glColor4d(*MarkColor)
        EnableAlphaBlend()
        glBegin(GL_QUADS)
        glVertex2d(MarkUL[0], MarkUL[1])
        glVertex2d(MarkLR[0], MarkUL[1])
        glVertex2d(MarkLR[0], MarkLR[1])
        glVertex2d(MarkUL[0], MarkLR[1])
        glEnd()
        # bright red frame
        glDisable(GL_BLEND)
        glBegin(GL_LINE_STRIP)
        glVertex2d(MarkUL[0], MarkUL[1])
        glVertex2d(MarkLR[0], MarkUL[1])
        glVertex2d(MarkLR[0], MarkLR[1])
        glVertex2d(MarkUL[0], MarkLR[1])
        glVertex2d(MarkUL[0], MarkUL[1])
        glEnd()
        glEnable(TextureTarget)

    # unapply the zoom transform
    glLoadIdentity()
    glOrtho(0.0, 1.0,  1.0, 0.0,  -10.0, 10.0)

    # Done.
    DrawOverlays()
    if do_flip:
        pygame.display.flip()

# draw a black screen with the Impressive logo at the center
def DrawLogo():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3ub(255, 255, 255)
    if not ShowLogo:
        return
    if HalfScreen:
        x0 = 0.25
    else:
        x0 = 0.5
    if TextureTarget != GL_TEXTURE_2D:
        glDisable(TextureTarget)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, LogoTexture)
    glBegin(GL_QUADS)
    glTexCoord2d(0, 0);  glVertex2d(x0 - 128.0 / ScreenWidth, 0.5 - 32.0 / ScreenHeight)
    glTexCoord2d(1, 0);  glVertex2d(x0 + 128.0 / ScreenWidth, 0.5 - 32.0 / ScreenHeight)
    glTexCoord2d(1, 1);  glVertex2d(x0 + 128.0 / ScreenWidth, 0.5 + 32.0 / ScreenHeight)
    glTexCoord2d(0, 1);  glVertex2d(x0 - 128.0 / ScreenWidth, 0.5 + 32.0 / ScreenHeight)
    glEnd()
    if OSDFont:
        OSDFont.Draw((int(ScreenWidth * x0), ScreenHeight / 2 + 48), \
                     __version__.split()[0], align=Center, alpha=0.25)
    glDisable(GL_TEXTURE_2D)

# draw the prerender progress bar
def DrawProgress(position):
    glDisable(TextureTarget)
    x0 = 0.1
    x2 = 1.0 - x0
    x1 = position * x2 + (1.0 - position) * x0
    y1 = 0.9
    y0 = y1 - 16.0 / ScreenHeight
    if HalfScreen:
        x0 *= 0.5
        x1 *= 0.5
        x2 *= 0.5
    glBegin(GL_QUADS)
    glColor3ub( 64,  64,  64);  glVertex2d(x0, y0);  glVertex2d(x2, y0)
    glColor3ub(128, 128, 128);  glVertex2d(x2, y1);  glVertex2d(x0, y1)
    glColor3ub( 64, 128, 255);  glVertex2d(x0, y0);  glVertex2d(x1, y0)
    glColor3ub(  8,  32, 128);  glVertex2d(x1, y1);  glVertex2d(x0, y1)
    glEnd()
    glEnable(TextureTarget)

# fade mode
def DrawFadeMode(intensity, alpha):
    if VideoPlaying: return
    DrawCurrentPage(do_flip=False)
    glDisable(TextureTarget)
    EnableAlphaBlend()
    glColor4d(intensity, intensity, intensity, alpha)
    DrawFullQuad()
    glEnable(TextureTarget)
    pygame.display.flip()

def EnterFadeMode(intensity=0.0):
    t0 = pygame.time.get_ticks()
    while True:
        if pygame.event.get([KEYDOWN,MOUSEBUTTONUP]): break
        t = (pygame.time.get_ticks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, t)
    DrawFadeMode(intensity, 1.0)

def LeaveFadeMode(intensity=0.0):
    t0 = pygame.time.get_ticks()
    while True:
        if pygame.event.get([KEYDOWN,MOUSEBUTTONUP]): break
        t = (pygame.time.get_ticks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, 1.0 - t)
    DrawCurrentPage()

def FadeMode(intensity):
    EnterFadeMode(intensity)
    while True:
        event = pygame.event.wait()
        if event.type == QUIT:
            PageLeft()
            Quit()
        elif event.type == VIDEOEXPOSE:
            DrawFadeMode(intensity, 1.0)
        elif event.type == MOUSEBUTTONUP:
            break
        elif event.type == KEYDOWN:
            if event.unicode == u'q':
                pygame.event.post(pygame.event.Event(QUIT))
            else:
                break
    LeaveFadeMode(intensity)

# gamma control
def SetGamma(new_gamma=None, new_black=None, force=False):
    global Gamma, BlackLevel
    if new_gamma is None: new_gamma = Gamma
    if new_gamma <  0.1:  new_gamma = 0.1
    if new_gamma > 10.0:  new_gamma = 10.0
    if new_black is None: new_black = BlackLevel
    if new_black <   0:   new_black = 0
    if new_black > 254:   new_black = 254
    if not(force) and (abs(Gamma - new_gamma) < 0.01) and (new_black == BlackLevel):
        return
    Gamma = new_gamma
    BlackLevel = new_black
    scale = 1.0 / (255 - BlackLevel)
    power = 1.0 / Gamma
    ramp = [int(65535.0 * ((max(0, x - BlackLevel) * scale) ** power)) for x in range(256)]
    return pygame.display.set_gamma_ramp(ramp, ramp, ramp)

# cursor image
def PrepareCustomCursor(cimg):
    global CursorTexture, CursorSX, CursorSY, CursorTX, CursorTY
    w, h = cimg.size
    tw, th = map(npot, cimg.size)
    if (tw > 256) or (th > 256):
        print >>sys.stderr, "Custom cursor is rediculously large, reverting to normal one."
        return False
    img = Image.new('RGBA', (tw, th))
    img.paste(cimg, (0, 0))
    CursorTexture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, CursorTexture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, img.tostring())
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    CursorSX = w * PixelX
    CursorSY = h * PixelY
    CursorTX = w / float(tw)
    CursorTY = h / float(th)
    return True
