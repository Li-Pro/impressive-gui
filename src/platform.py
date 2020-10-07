##### PLATFORM-SPECIFIC PYGAME INTERFACE CODE ##################################

class Platform_PyGame(object):
    name = 'pygame'
    allow_custom_fullscreen_res = True
    has_hardware_cursor = True
    use_omxplayer = False

    _buttons = { 1: "lmb", 2: "mmb", 3: "rmb", 4: "wheelup", 5: "wheeldown" }
    _keys = dict((getattr(pygame.locals, k), k[2:].lower()) for k in [k for k in dir(pygame.locals) if k.startswith('K_')])

    def __init__(self):
        self.next_events = []
        self.schedule_map_ev2flag = {}
        self.schedule_map_ev2name = {}
        self.schedule_map_name2ev = {}
        self.schedule_max = USEREVENT

    def Init(self):
        os.environ["SDL_MOUSE_RELATIVE"] = "0"
        pygame.display.init()

    def GetTicks(self):
        return pygame.time.get_ticks()

    def GetScreenSize(self):
        return pygame.display.list_modes()[0]

    def StartDisplay(self):
        global ScreenWidth, ScreenHeight, Fullscreen, FakeFullscreen, WindowPos
        pygame.display.set_caption(__title__)
        flags = OPENGL | DOUBLEBUF
        if Fullscreen:
            if FakeFullscreen:
                print("Using \"fake-fullscreen\" mode.", file=sys.stderr)
                flags |= NOFRAME
                if not WindowPos:
                    WindowPos = (0,0)
            else:
                flags |= FULLSCREEN
        if WindowPos:
            os.environ["SDL_VIDEO_WINDOW_POS"] = ','.join(map(str, WindowPos))
        pygame.display.set_mode((ScreenWidth, ScreenHeight), flags)
        pygame.key.set_repeat(500, 30)

    def LoadOpenGL(self):
        sdl = None
        
        # PyGame installations done with pip may come with its own SDL library,
        # in which case we must not use the default system-wide SDL;
        # so we need to find out the local library's path
        try:
            pattern = re.compile(r'(lib)?SDL(?!_[a-zA-Z]+).*?\.(dll|so(\..*)?|dylib)$', re.I)
            libs = []
            for suffix in (".libs", ".dylibs"):
                libdir = os.path.join(pygame.__path__[0], suffix)
                if os.path.isdir(libdir):
                    libs += [os.path.join(libdir, lib) for lib in sorted(os.listdir(libdir)) if pattern.match(lib)]
            sdl = libs.pop(0)
        except (IndexError, AttributeError, EnvironmentError):
            pass

        # generic case: load the system-wide SDL
        sdl = sdl or ctypes.util.find_library("SDL") or ctypes.util.find_library("SDL-1.2") or "SDL"

        # load the library
        try:
            sdl = CDLL(sdl, RTLD_GLOBAL)
            get_proc_address = CFUNCTYPE(c_void_p, c_char_p)(('SDL_GL_GetProcAddress', sdl))
        except OSError:
            raise ImportError("failed to load the SDL library")
        except AttributeError:
            raise ImportError("failed to load SDL_GL_GetProcAddress from the SDL library")

        # load the symbols
        def loadsym(name, prototype):
            try:
                addr = get_proc_address(name.encode())
            except EnvironmentError:
                return None
            if not addr:
                return None
            return prototype(addr)
        return OpenGL(loadsym, desktop=True)

    def SwapBuffers(self):
        pygame.display.flip()

    def Done(self):
        pygame.display.quit()
    def Quit(self):
        pygame.quit()

    def SetWindowTitle(self, text):
        try:
            pygame.display.set_caption(text, __title__)
        except UnicodeEncodeError:
            pygame.display.set_caption(text.encode('utf-8'), __title__)
    def GetWindowID(self):
        return pygame.display.get_wm_info()['window']

    def GetMousePos(self):
        return pygame.mouse.get_pos()
    def SetMousePos(self, coords):
        pygame.mouse.set_pos(coords)
    def SetMouseVisible(self, visible):
        pygame.mouse.set_visible(visible)

    def _translate_mods(self, key, mods):
        if mods & KMOD_SHIFT:
            key = "shift+" + key
        if mods & KMOD_ALT:
            key = "alt+" + key
        if mods & KMOD_CTRL:
            key = "ctrl+" + key
        return key
    def _translate_button(self, ev):
        try:
            return self._translate_mods(self._buttons[ev.button], pygame.key.get_mods())
        except KeyError:
            return 'btn' + str(ev.button)
    def _translate_key(self, ev):
        try:
            return self._translate_mods(self._keys[ev.key], ev.mod)
        except KeyError:
            return 'unknown-key-' + str(ev.key)

    def _translate_event(self, ev):
        if ev.type == QUIT:
            return ["$quit"]
        elif ev.type == VIDEOEXPOSE:
            return ["$expose"]
        elif ev.type == MOUSEBUTTONDOWN:
            return ['+' + self._translate_button(ev)]
        elif ev.type == MOUSEBUTTONUP:
            ev = self._translate_button(ev)
            return ['*' + ev, '-' + ev]
        elif ev.type == MOUSEMOTION:
            pygame.event.clear(MOUSEMOTION)
            return ["$move"]
        elif ev.type == KEYDOWN:
            if ev.mod & KMOD_ALT:
                if ev.key == K_F4:
                    return self.PostQuitEvent()
                elif ev.key == K_TAB:
                    return "$alt-tab"
            ev = self._translate_key(ev)
            return ['+' + ev, '*' + ev]
        elif ev.type == KEYUP:
            return ['-' + self._translate_key(ev)]
        elif (ev.type >= USEREVENT) and (ev.type < self.schedule_max):
            if not(self.schedule_map_ev2flag.get(ev.type)):
                pygame.time.set_timer(ev.type, 0)
            return [self.schedule_map_ev2name.get(ev.type)]
        elif (ev.type == ACTIVEEVENT) and (ev.state == 1):  # APPMOUSEFOCUS=1
            return ["$enter" if ev.gain else "$leave"]
        else:
            return []

    def GetEvent(self, poll=False):
        if self.next_events:
            return self.next_events.pop(0)
        if poll:
            ev = pygame.event.poll()
        else:
            ev = pygame.event.wait()
        evs = self._translate_event(ev)
        if evs:
            self.next_events.extend(evs[1:])
            return evs[0]

    def CheckAnimationCancelEvent(self):
        while True:
            ev = pygame.event.poll()
            if ev.type == NOEVENT:
                break
            self.next_events.extend(self._translate_event(ev))
            if ev.type in set([KEYDOWN, MOUSEBUTTONUP, QUIT]):
                return True

    def ScheduleEvent(self, name, msec=0, periodic=False):
        try:
            ev_code = self.schedule_map_name2ev[name]
        except KeyError:
            ev_code = self.schedule_max
            self.schedule_map_name2ev[name] = ev_code
            self.schedule_map_ev2name[ev_code] = name
            self.schedule_max += 1
        self.schedule_map_ev2flag[ev_code] = periodic
        pygame.time.set_timer(ev_code, msec)

    def PostQuitEvent(self):
        pygame.event.post(pygame.event.Event(QUIT))

    def ToggleFullscreen(self):
        return pygame.display.toggle_fullscreen()

    def Minimize(self):
        pygame.display.iconify()

    def SetGammaRamp(self, gamma, black_level):
        scale = 1.0 / (255 - black_level)
        power = 1.0 / gamma
        ramp = [int(65535.0 * ((max(0, x - black_level) * scale) ** power)) for x in range(256)]
        return pygame.display.set_gamma_ramp(ramp, ramp, ramp)


class Platform_Win32(Platform_PyGame):
    name = 'pygame-win32'

    def GetScreenSize(self):
        if HaveWin32API:
            dm = win32api.EnumDisplaySettings(None, -1) #ENUM_CURRENT_SETTINGS
            return (int(dm.PelsWidth), int(dm.PelsHeight))
        return Platform_PyGame.GetScreenSize(self)

    def LoadOpenGL(self):
        try:
            opengl32 = WinDLL("opengl32")
            get_proc_address = WINFUNCTYPE(c_void_p, c_char_p)(('wglGetProcAddress', opengl32))
        except OSError:
            raise ImportError("failed to load the OpenGL library")
        except AttributeError:
            raise ImportError("failed to load wglGetProcAddress from the OpenGL library")
        def loadsym(name, prototype):
            # try to load OpenGL 1.1 function from opengl32.dll first
            try:
                return prototype((name, opengl32))
            except AttributeError:
                pass
            # if that fails, load the extension function via wglGetProcAddress
            try:
                addr = get_proc_address(name.encode())
            except EnvironmentError:
                addr = None
            if not addr:
                return None
            return prototype(addr)
        return OpenGL(loadsym, desktop=True)


class Platform_Unix(Platform_PyGame):
    name = 'pygame-unix'

    def GetScreenSize(self):
        re_res = re.compile(r'\s*(\d+)x(\d+)\s+\d+\.\d+\*')
        res = None
        try:
            xrandr = Popen(["xrandr"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in xrandr.stdout:
                m = re_res.match(line.decode())
                if m:
                    res = tuple(map(int, m.groups()))
            xrandr.wait()
        except OSError:
            pass
        if res:
            return res
        return Platform_PyGame.GetScreenSize(self)


class Platform_RasPi4(Platform_Unix):
    use_omxplayer = True


class Platform_EGL(Platform_Unix):
    name = 'egl'
    egllib = "EGL"
    gles2lib = "GLESv2"

    def StartDisplay(self, display=None, window=None, width=None, height=None):
        global ScreenWidth, ScreenHeight
        width  = width  or ScreenWidth
        height = height or ScreenHeight

        # load the GLESv2 library before the EGL library (required on the BCM2835)
        try:
            self.gles = ctypes.CDLL(ctypes.util.find_library(self.gles2lib))
        except OSError:
            raise ImportError("failed to load the OpenGL ES 2.0 library")

        # import all functions first
        try:
            egl = CDLL(ctypes.util.find_library(self.egllib))
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, egl))
            eglGetDisplay = loadfunc("eglGetDisplay", c_void_p, c_void_p)
            eglInitialize = loadfunc("eglInitialize", c_uint, c_void_p, POINTER(c_int), POINTER(c_int))
            eglChooseConfig = loadfunc("eglChooseConfig", c_uint, c_void_p, c_void_p, POINTER(c_void_p), c_int, POINTER(c_int))
            eglCreateWindowSurface = loadfunc("eglCreateWindowSurface", c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)
            eglCreateContext = loadfunc("eglCreateContext", c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)
            eglMakeCurrent = loadfunc("eglMakeCurrent", c_uint, c_void_p, c_void_p, c_void_p, c_void_p)
            self.eglSwapBuffers = loadfunc("eglSwapBuffers", c_int, c_void_p, c_void_p)
        except OSError:
            raise ImportError("failed to load the EGL library")
        except AttributeError:
            raise ImportError("failed to load required symbols from the EGL library")

        # prepare parameters
        config_attribs = [
            0x3024, 8,      # EGL_RED_SIZE >= 8
            0x3023, 8,      # EGL_GREEN_SIZE >= 8
            0x3022, 8,      # EGL_BLUE_SIZE >= 8
            0x3021, 0,      # EGL_ALPHA_SIZE >= 0
            0x3025, 0,      # EGL_DEPTH_SIZE >= 0
            0x3040, 0x0004, # EGL_RENDERABLE_TYPE = EGL_OPENGL_ES2_BIT
            0x3033, 0x0004, # EGL_SURFACE_TYPE = EGL_WINDOW_BIT
            0x3038          # EGL_NONE
        ]
        context_attribs = [
            0x3098, 2,      # EGL_CONTEXT_CLIENT_VERSION = 2
            0x3038          # EGL_NONE
        ]
        config_attribs = (c_int * len(config_attribs))(*config_attribs)
        context_attribs = (c_int * len(context_attribs))(*context_attribs)

        # perform actual initialization
        eglMakeCurrent(None, None, None, None)
        self.egl_display = eglGetDisplay(display)
        if not self.egl_display:
            raise RuntimeError("could not get EGL display")
        if not eglInitialize(self.egl_display, None, None):
            raise RuntimeError("could not initialize EGL")
        config = c_void_p()
        num_configs = c_int(0)
        if not eglChooseConfig(self.egl_display, config_attribs, byref(config), 1, byref(num_configs)):
            raise RuntimeError("failed to get a framebuffer configuration")
        if not num_configs.value:
            raise RuntimeError("no suitable framebuffer configuration found")
        self.egl_surface = eglCreateWindowSurface(self.egl_display, config, window, None)
        if not self.egl_surface:
            raise RuntimeError("could not create EGL surface")
        context = eglCreateContext(self.egl_display, config, None, context_attribs)
        if not context:
            raise RuntimeError("could not create OpenGL ES rendering context")
        if not eglMakeCurrent(self.egl_display, self.egl_surface, self.egl_surface, context):
            raise RuntimeError("could not activate OpenGL ES rendering context")

    def LoadOpenGL(self):
        def loadsym(name, prototype):
            return prototype((name, self.gles))
        return OpenGL(loadsym, desktop=False)

    def SwapBuffers(self):
        self.eglSwapBuffers(self.egl_display, self.egl_surface)


class Platform_BCM2835(Platform_EGL):
    name = 'bcm2835'
    allow_custom_fullscreen_res = False
    has_hardware_cursor = False
    use_omxplayer = True
    egllib = "brcmEGL"
    gles2lib = "brcmGLESv2"
    DISPLAY_ID = 0

    def __init__(self, libbcm_host):
        Platform_EGL.__init__(self)
        self.libbcm_host_path = libbcm_host

    def Init(self):
        try:
            self.bcm_host = CDLL(self.libbcm_host_path)
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, self.bcm_host))
            bcm_host_init = loadfunc("bcm_host_init", None)
            graphics_get_display_size = loadfunc("graphics_get_display_size", c_int32, c_uint16, POINTER(c_uint32), POINTER(c_uint32))
        except OSError:
            raise ImportError("failed to load the bcm_host library")
        except AttributeError:
            raise ImportError("failed to load required symbols from the bcm_host library")
        bcm_host_init()
        x, y = c_uint32(0), c_uint32(0)
        if graphics_get_display_size(self.DISPLAY_ID, byref(x), byref(y)) < 0:
            raise RuntimeError("could not determine display size")
        self.screen_size = (int(x.value), int(y.value))

    def GetScreenSize(self):
        return self.screen_size

    def StartDisplay(self):
        global ScreenWidth, ScreenHeight, Fullscreen, FakeFullscreen, WindowPos
        class VC_DISPMANX_ALPHA_T(Structure):
            _fields_ = [("flags", c_int), ("opacity", c_uint32), ("mask", c_void_p)]
        class EGL_DISPMANX_WINDOW_T(Structure):
            _fields_ = [("element", c_uint32), ("width", c_int), ("height", c_int)]

        # first, import everything
        try:
            def loadfunc(func, ret, *args):
                return CFUNCTYPE(ret, *args)((func, self.bcm_host))
            vc_dispmanx_display_open = loadfunc("vc_dispmanx_display_open", c_uint32, c_uint32)
            vc_dispmanx_update_start = loadfunc("vc_dispmanx_update_start", c_uint32, c_int32)
            vc_dispmanx_element_add = loadfunc("vc_dispmanx_element_add", c_int32,
                c_uint32, c_uint32, c_int32,  # update, display, layer
                c_void_p, c_uint32, c_void_p, c_uint32,  # dest_rect, src, drc_rect, protection
                POINTER(VC_DISPMANX_ALPHA_T),  # alpha
                c_void_p, c_uint32)  # clamp, transform
            vc_dispmanx_update_submit_sync = loadfunc("vc_dispmanx_update_submit_sync", c_int, c_uint32)
        except AttributeError:
            raise ImportError("failed to load required symbols from the bcm_host library")

        # sanitize arguments
        width  = min(ScreenWidth,  self.screen_size[0])
        height = min(ScreenHeight, self.screen_size[1])
        if WindowPos:
            x0, y0 = WindowPos
        else:
            x0 = (self.screen_size[0] - width)  // 2
            y0 = (self.screen_size[1] - height) // 2
        x0 = max(min(x0, self.screen_size[0] - width),  0)
        y0 = max(min(y0, self.screen_size[1] - height), 0)

        # prepare arguments
        dst_rect = (c_int32 * 4)(x0, y0, width, height)
        src_rect = (c_int32 * 4)(0, 0, width << 16, height << 16)
        alpha = VC_DISPMANX_ALPHA_T(1, 255, None)  # DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS

        # perform initialization
        display = vc_dispmanx_display_open(self.DISPLAY_ID)
        update = vc_dispmanx_update_start(0)
        layer = vc_dispmanx_element_add(update, display, 0, byref(dst_rect), 0, byref(src_rect), 0, byref(alpha), None, 0)
        vc_dispmanx_update_submit_sync(update)
        self.window = EGL_DISPMANX_WINDOW_T(layer, width, height)
        Platform_EGL.StartDisplay(self, None, byref(self.window), width, height)

        # finally, tell PyGame what just happened
        pygame.display.set_mode((width, height), 0)
        pygame.mouse.set_pos((width // 2, height // 2))


libbcm_host = ctypes.util.find_library("bcm_host")
if libbcm_host:
    try:
        with open("/sys/firmware/devicetree/base/model") as f:
            model = f.read()
    except EnvironmentError:
        model = ""
    m = re.search(r'pi\s*(\d+)', model, flags=re.I)
    if m and (int(m.group(1)) >= 4):
        Platform = Platform_RasPi4()
    else:
        Platform = Platform_BCM2835(libbcm_host)
elif os.name == "nt":
    Platform = Platform_Win32()
else:
    Platform = Platform_Unix()
