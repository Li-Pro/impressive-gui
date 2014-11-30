##### OPENGL RENDERING #########################################################

# draw OSD overlays
def DrawOverlays(trans_time=0.0):
    reltime = Platform.GetTicks() - StartTime
    gl.Enable(gl.BLEND)

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
        ProgressBarShader.get_instance().draw(
            zero, 1.0 - ProgressBarSizeFactor,
            rel,  1.0,
            color0=(r, g, b, 0.0),
            color1=(r, g, b, a)
        )

    OSDFont.BeginDraw()
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
    OSDFont.EndDraw()

    if CursorImage and CursorVisible:
        x, y = Platform.GetMousePos()
        x -= CursorHotspot[0]
        y -= CursorHotspot[1]
        X0 = x * PixelX
        Y0 = y * PixelY
        X1 = X0 + CursorSX
        Y1 = Y0 + CursorSY
        TexturedRectShader.get_instance().draw(
            X0, Y0, X1, Y1,
            s1=CursorTX, t1=CursorTY,
            tex=CursorTexture
        )

    gl.Disable(gl.BLEND)


# draw the complete image of the current page
def DrawCurrentPage(dark=1.0, do_flip=True):
    global ScreenTransform
    if VideoPlaying: return
    boxes = GetPageProp(Pcurrent, 'boxes')
    gl.Clear(gl.COLOR_BUFFER_BIT)

    # pre-transform for zoom
    if ZoomArea != 1.0:
        ScreenTransform = (
            -2.0 * ZoomX0 / ZoomArea - 1.0,
            +2.0 * ZoomY0 / ZoomArea + 1.0,
            +2.0 / ZoomArea,
            -2.0 / ZoomArea
        )

    # background layer -- the page's image, darkened if it has boxes
    is_dark = (boxes or Tracing) and (dark > 0.001)
    if not is_dark:
        # standard mode
        TexturedRectShader.get_instance().draw(
            0.0, 0.0, 1.0, 1.0,
            s1=TexMaxS, t1=TexMaxT,
            tex=Tcurrent
        )
    elif UseBlurShader:
        # blurred background (using shader)
        blur_scale = BoxFadeBlur * ZoomArea * dark
        BlurShader.get_instance().draw(
            PixelX * blur_scale,
            PixelY * blur_scale,
            1.0 - BoxFadeDarkness * dark,
            tex=Tcurrent
        )
        gl.Enable(gl.BLEND)
        # note: BLEND stays enabled during the rest of this function;
        # it will be disabled at the end of DrawOverlays()
    else:
        # blurred background (using oldschool multi-pass blend fallback)
        intensity = 1.0 - BoxFadeDarkness * dark
        for dx, dy, alpha in (
            (0.0,  0.0, 1.0),
            (-ZoomArea, 0.0, dark / 2),
            (+ZoomArea, 0.0, dark / 3),
            (0.0, -ZoomArea, dark / 4),
            (0.0, +ZoomArea, dark / 5),
        ):
            TexturedRectShader.get_instance().draw(
                0.0, 0.0, 1.0, 1.0,
                TexMaxS *  PixelX * dx,
                TexMaxT *  PixelY * dy,
                TexMaxS * (PixelX * dx + 1.0),
                TexMaxT * (PixelY * dy + 1.0),
                tex=Tcurrent,
                color=(intensity, intensity, intensity, alpha)
            )
            gl.Enable(gl.BLEND)
        

    if boxes and is_dark:
        TexturedMeshShader.get_instance().setup(
            0.0, 0.0, 1.0, 1.0,
            s1=TexMaxS, t1=TexMaxT
            # tex is already set
        )
        for X0, Y0, X1, Y1 in boxes:
            vertices = (c_float * 27)(
                X0, Y0, 1.0,  # note: this produces two degenerate triangles
                X0,         Y0,         1.0,
                X0 - EdgeX, Y0 - EdgeY, 0.0,
                X1,         Y0,         1.0,
                X1 + EdgeX, Y0 - EdgeY, 0.0,
                X1,         Y1,         1.0,
                X1 + EdgeX, Y1 + EdgeY, 0.0,
                X0,         Y1,         1.0,
                X0 - EdgeX, Y1 + EdgeY, 0.0,
            )
            gl.BindBuffer(gl.ARRAY_BUFFER, 0)
            gl.VertexAttribPointer(0, 3, gl.FLOAT, False, 0, vertices)
            BoxIndexBuffer.draw()

    if Tracing and is_dark:
        x, y = MouseToScreen(Platform.GetMousePos())
        TexturedMeshShader.get_instance().setup(
            x, y, x + 1.0, y + 1.0,
            x * TexMaxS, y * TexMaxT,
            (x + 1.0) * TexMaxS, (y + 1.0) * TexMaxT
            # tex is already set
        )
        gl.BindBuffer(gl.ARRAY_BUFFER, SpotVertices)
        gl.VertexAttribPointer(0, 3, gl.FLOAT, False, 0, 0)
        SpotIndices.draw()

    if Marking:
        x0 = min(MarkUL[0], MarkLR[0])
        y0 = min(MarkUL[1], MarkLR[1])
        x1 = max(MarkUL[0], MarkLR[0])
        y1 = max(MarkUL[1], MarkLR[1])
        # red frame (misusing the progress bar shader as a single-color shader)
        color = (MarkColor[0], MarkColor[1], MarkColor[2], 1.0)
        ProgressBarShader.get_instance().draw(
            x0 - PixelX * ZoomArea, y0 - PixelY * ZoomArea,
            x1 + PixelX * ZoomArea, y1 + PixelY * ZoomArea,
            color0=color, color1=color
        )
        # semi-transparent inner area
        gl.Enable(gl.BLEND)
        TexturedRectShader.get_instance().draw(
            x0, y0, x1, y1,
            x0 * TexMaxS, y0 * TexMaxT,
            x1 * TexMaxS, y1 * TexMaxT,
            tex=Tcurrent, color=(1.0, 1.0, 1.0, 1.0 - MarkColor[3])
        )

    # unapply the zoom transform
    ScreenTransform = DefaultScreenTransform

    # Done.
    DrawOverlays()
    if do_flip:
        Platform.SwapBuffers()

# draw a black screen with the Impressive logo at the center
def DrawLogo():
    gl.Clear(gl.COLOR_BUFFER_BIT)
    if not ShowLogo:
        return
    if HalfScreen:
        x0 = 0.25
    else:
        x0 = 0.5
    TexturedRectShader.get_instance().draw(
        x0 - 128.0 / ScreenWidth,  0.5 - 32.0 / ScreenHeight,
        x0 + 128.0 / ScreenWidth,  0.5 + 32.0 / ScreenHeight,
        tex=LogoTexture
    )
    if OSDFont:
        gl.Enable(gl.BLEND)
        OSDFont.Draw((int(ScreenWidth * x0), ScreenHeight / 2 + 48), \
                     __version__.split()[0], align=Center, alpha=0.25, beveled=False)
        gl.Disable(gl.BLEND)

# draw the prerender progress bar
def DrawProgress(position):
    x0 = 0.1
    x2 = 1.0 - x0
    x1 = position * x2 + (1.0 - position) * x0
    y1 = 0.9
    y0 = y1 - 16.0 / ScreenHeight
    if HalfScreen:
        x0 *= 0.5
        x1 *= 0.5
        x2 *= 0.5
    ProgressBarShader.get_instance().draw(
        x0, y0, x2, y1,
        color0=(0.25, 0.25, 0.25, 1.0),
        color1=(0.50, 0.50, 0.50, 1.0)
    )
    ProgressBarShader.get_instance().draw(
        x0, y0, x1, y1,
        color0=(0.25, 0.50, 1.00, 1.0),
        color1=(0.03, 0.12, 0.50, 1.0)
    )

# fade mode
def DrawFadeMode(intensity, alpha):
    if VideoPlaying: return
    DrawCurrentPage(do_flip=False)
    gl.Enable(gl.BLEND)
    color = (intensity, intensity, intensity, alpha)
    ProgressBarShader.get_instance().draw(
        0.0, 0.0, 1.0, 1.0,
        color0=color, color1=color
    )
    gl.Disable(gl.BLEND)
    Platform.SwapBuffers()

def EnterFadeMode(intensity=0.0):
    t0 = Platform.GetTicks()
    while True:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, t)
    DrawFadeMode(intensity, 1.0)

def LeaveFadeMode(intensity=0.0):
    t0 = Platform.GetTicks()
    while True:
        if Platform.CheckAnimationCancelEvent(): break
        t = (Platform.GetTicks() - t0) * 1.0 / BlankFadeDuration
        if t >= 1.0: break
        DrawFadeMode(intensity, 1.0 - t)
    DrawCurrentPage()

def FadeMode(intensity):
    EnterFadeMode(intensity)
    def fade_action_handler(action):
        if action == "$quit":
            PageLeft()
            Quit()
        elif action == "$expose":
            DrawFadeMode(intensity, 1.0)
        elif action == "*quit":
            Platform.PostQuitEvent()
        else:
            return False
        return True
    while True:
        ev = Platform.GetEvent()
        if ev and not(ProcessEvent(ev, fade_action_handler)) and ev.startswith('*'):
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
    return Platform.SetGammaRamp(new_gamma, new_black)

# cursor image
def PrepareCustomCursor(cimg):
    global CursorTexture, CursorHotspot, CursorSX, CursorSY, CursorTX, CursorTY
    if not cimg:
        CursorHotspot = (1,0)
        cimg = Image.open(cStringIO.StringIO(DEFAULT_CURSOR.decode('base64')))
    w, h = cimg.size
    tw, th = map(npot, cimg.size)
    if (tw > 256) or (th > 256):
        print >>sys.stderr, "Custom cursor is ridiculously large, reverting to normal one."
        return False
    img = Image.new('RGBA', (tw, th))
    img.paste(cimg, (0, 0))
    CursorTexture = gl.make_texture(gl.TEXTURE_2D, gl.CLAMP_TO_EDGE, gl.NEAREST)
    gl.load_texture(gl.TEXTURE_2D, img)
    CursorSX = w * PixelX
    CursorSY = h * PixelY
    CursorTX = w / float(tw)
    CursorTY = h / float(th)
    return True
