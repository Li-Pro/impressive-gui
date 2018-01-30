##### OPENGL (ES) 2.0 LOADER AND TOOLKIT #######################################

if os.name == 'nt':
    GLFUNCTYPE = WINFUNCTYPE
else:
    GLFUNCTYPE = CFUNCTYPE

class GLFunction(object):
    def __init__(self, required, name, ret, *args):
        self.name = name
        self.required = required
        self.prototype = GLFUNCTYPE(ret, *args)

class OpenGL(object):
    FALSE = 0
    TRUE = 1
    NO_ERROR = 0
    INVALID_ENUM = 0x0500
    INVALID_VALUE = 0x0501
    INVALID_OPERATION = 0x0502
    OUT_OF_MEMORY = 0x0505
    INVALID_FRAMEBUFFER_OPERATION = 0x0506
    VENDOR = 0x1F00
    RENDERER = 0x1F01
    VERSION = 0x1F02
    EXTENSIONS = 0x1F03
    POINTS = 0x0000
    LINES = 0x0001
    LINE_LOOP = 0x0002
    LINE_STRIP = 0x0003
    TRIANGLES = 0x0004
    TRIANGLE_STRIP = 0x0005
    TRIANGLE_FAN = 0x0006
    BYTE = 0x1400
    UNSIGNED_BYTE = 0x1401
    SHORT = 0x1402
    UNSIGNED_SHORT = 0x1403
    INT = 0x1404
    UNSIGNED_INT = 0x1405
    FLOAT = 0x1406
    DEPTH_TEST = 0x0B71
    BLEND = 0x0BE2
    ZERO = 0
    ONE = 1
    SRC_COLOR = 0x0300
    ONE_MINUS_SRC_COLOR = 0x0301
    SRC_ALPHA = 0x0302
    ONE_MINUS_SRC_ALPHA = 0x0303
    DST_ALPHA = 0x0304
    ONE_MINUS_DST_ALPHA = 0x0305
    DST_COLOR = 0x0306
    ONE_MINUS_DST_COLOR = 0x0307
    DEPTH_BUFFER_BIT = 0x00000100
    COLOR_BUFFER_BIT = 0x00004000
    TEXTURE0 = 0x84C0
    TEXTURE_2D = 0x0DE1
    TEXTURE_RECTANGLE = 0x84F5
    TEXTURE_MAG_FILTER = 0x2800
    TEXTURE_MIN_FILTER = 0x2801
    TEXTURE_WRAP_S = 0x2802
    TEXTURE_WRAP_T = 0x2803
    NEAREST = 0x2600
    LINEAR = 0x2601
    NEAREST_MIPMAP_NEAREST = 0x2700
    LINEAR_MIPMAP_NEAREST = 0x2701
    NEAREST_MIPMAP_LINEAR = 0x2702
    LINEAR_MIPMAP_LINEAR = 0x2703
    CLAMP_TO_EDGE = 0x812F
    REPEAT = 0x2901
    ALPHA = 0x1906
    RGB = 0x1907
    RGBA = 0x1908
    LUMINANCE = 0x1909
    LUMINANCE_ALPHA = 0x190A
    ARRAY_BUFFER = 0x8892
    ELEMENT_ARRAY_BUFFER = 0x8893
    STREAM_DRAW = 0x88E0
    STATIC_DRAW = 0x88E4
    DYNAMIC_DRAW = 0x88E8
    FRAGMENT_SHADER = 0x8B30
    VERTEX_SHADER = 0x8B31
    COMPILE_STATUS = 0x8B81
    LINK_STATUS = 0x8B82
    INFO_LOG_LENGTH = 0x8B84
    UNPACK_ALIGNMENT = 0x0CF5
    _funcs = [
        GLFunction(True,  "GetString",                c_char_p, c_uint),
        GLFunction(True,  "Enable",                   None, c_uint),
        GLFunction(True,  "Disable",                  None, c_uint),
        GLFunction(True,  "GetError",                 c_uint),
        GLFunction(True,  "Viewport",                 None, c_int, c_int, c_int, c_int),
        GLFunction(True,  "Clear",                    None, c_uint),
        GLFunction(True,  "ClearColor",               None, c_float, c_float, c_float, c_float),
        GLFunction(True,  "BlendFunc",                None, c_uint, c_uint),
        GLFunction(True,  "GenTextures",              None, c_uint, POINTER(c_int)),
        GLFunction(True,  "BindTexture",              None, c_uint, c_int),
        GLFunction(True,  "ActiveTexture",            None, c_uint),
        GLFunction(True,  "TexParameteri",            None, c_uint, c_uint, c_int),
        GLFunction(True,  "TexImage2D",               None, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_uint, c_void_p),
        GLFunction(True,  "GenerateMipmap",           None, c_uint),
        GLFunction(True,  "GenBuffers",               None, c_uint, POINTER(c_int)),
        GLFunction(True,  "BindBuffer",               None, c_uint, c_int),
        GLFunction(True,  "BufferData",               None, c_uint, c_void_p, c_void_p, c_uint),
        GLFunction(True,  "CreateProgram",            c_uint),
        GLFunction(True,  "CreateShader",             c_uint, c_uint),
        GLFunction(True,  "ShaderSource",             None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "CompileShader",            None, c_uint),
        GLFunction(True,  "GetShaderiv",              None, c_uint, c_uint, POINTER(c_uint)),
        GLFunction(True,  "GetShaderInfoLog",         None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "AttachShader",             None, c_uint, c_uint),
        GLFunction(True,  "LinkProgram",              None, c_uint),
        GLFunction(True,  "GetProgramiv",             None, c_uint, c_uint, POINTER(c_uint)),
        GLFunction(True,  "GetProgramInfoLog",        None, c_uint, c_uint, c_void_p, c_void_p),
        GLFunction(True,  "UseProgram",               None, c_uint),
        GLFunction(True,  "BindAttribLocation",       None, c_uint, c_uint, c_char_p),
        GLFunction(True,  "GetAttribLocation",        c_int, c_uint, c_char_p),
        GLFunction(True,  "GetUniformLocation",       c_int, c_uint, c_char_p),
        GLFunction(True,  "Uniform1f",                None, c_uint, c_float),
        GLFunction(True,  "Uniform2f",                None, c_uint, c_float, c_float),
        GLFunction(True,  "Uniform3f",                None, c_uint, c_float, c_float, c_float),
        GLFunction(True,  "Uniform4f",                None, c_uint, c_float, c_float, c_float, c_float),
        GLFunction(True,  "Uniform1i",                None, c_uint, c_int),
        GLFunction(True,  "Uniform2i",                None, c_uint, c_int, c_int),
        GLFunction(True,  "Uniform3i",                None, c_uint, c_int, c_int, c_int),
        GLFunction(True,  "Uniform4i",                None, c_uint, c_int, c_int, c_int, c_int),
        GLFunction(True,  "EnableVertexAttribArray",  None, c_uint),
        GLFunction(True,  "DisableVertexAttribArray", None, c_uint),
        GLFunction(True,  "VertexAttribPointer",      None, c_uint, c_uint, c_uint, c_uint, c_uint, c_void_p),
        GLFunction(True,  "DrawArrays",               None, c_uint, c_uint, c_uint),
        GLFunction(True,  "DrawElements",             None, c_uint, c_uint, c_uint, c_void_p),
        GLFunction(True,  "PixelStorei",              None, c_uint, c_uint),
    ]
    _typemap = {
                  BYTE:  c_int8,
         UNSIGNED_BYTE: c_uint8,
                 SHORT:  c_int16,
        UNSIGNED_SHORT: c_uint16,
                   INT:  c_int32,
          UNSIGNED_INT: c_uint32,
                 FLOAT:  c_float
    }

    def __init__(self, loader, desktop=False):
        global GLVendor, GLRenderer, GLVersion
        self._is_desktop_gl = desktop
        for func in self._funcs:
            funcptr = None
            for suffix in ("", "ARB", "ObjectARB", "EXT", "OES"):
                funcptr = loader("gl" + func.name + suffix, func.prototype)
                if funcptr:
                    break
            if not funcptr:
                if func.required:
                    raise ImportError("failed to import required OpenGL function 'gl%s'" % func.name)
                else:
                    def errfunc(*args):
                        raise ImportError("call to unimplemented OpenGL function 'gl%s'" % func.name)
                    funcptr = errfunc
            if hasattr(self, func.name):
                setattr(self, '_' + func.name, funcptr)
            else:
                setattr(self, func.name, funcptr)
            if func.name == "GetString":
                GLVendor = self.GetString(self.VENDOR) or ""
                GLRenderer = self.GetString(self.RENDERER) or ""
                GLVersion = self.GetString(self.VERSION) or ""
        self._init()

    def GenTextures(self, n=1):
        bufs = (c_int * n)()
        self._GenTextures(n, bufs)
        if n == 1: return bufs[0]
        return list(bufs)

    def ActiveTexture(self, tmu):
        if tmu < self.TEXTURE0:
            tmu += self.TEXTURE0
        self._ActiveTexture(tmu)

    def GenBuffers(self, n=1):
        bufs = (c_int * n)()
        self._GenBuffers(n, bufs)
        if n == 1: return bufs[0]
        return list(bufs)

    def BufferData(self, target, size=0, data=None, usage=STATIC_DRAW, type=None):
        if isinstance(data, list):
            if type:
                type = self._typemap[type]
            elif isinstance(data[0], int):
                type = c_int32
            elif isinstance(data[0], float):
                type = c_float
            else:
                raise TypeError("cannot infer buffer data type")
            size = len(data) * sizeof(type)
            data = (type * len(data))(*data)
        self._BufferData(target, cast(size, c_void_p), cast(data, c_void_p), usage)

    def ShaderSource(self, shader, source):
        source = c_char_p(source)
        self._ShaderSource(shader, 1, pointer(source), None)

    def GetShaderi(self, shader, pname):
        res = (c_uint * 1)()
        self.GetShaderiv(shader, pname, res)
        return res[0]

    def GetShaderInfoLog(self, shader):
        length = self.GetShaderi(shader, self.INFO_LOG_LENGTH)
        if not length: return ""
        buf = create_string_buffer(length + 1)
        self._GetShaderInfoLog(shader, length + 1, None, buf)
        return buf.raw.split('\0', 1)[0]

    def GetProgrami(self, program, pname):
        res = (c_uint * 1)()
        self.GetProgramiv(program, pname, res)
        return res[0]

    def GetProgramInfoLog(self, program):
        length = self.GetProgrami(program, self.INFO_LOG_LENGTH)
        if not length: return ""
        buf = create_string_buffer(length + 1)
        self._GetProgramInfoLog(program, length + 1, None, buf)
        return buf.raw.split('\0', 1)[0]

    def Uniform(self, location, *values):
        if not values:
            raise TypeError("no values for glUniform")
        if (len(values) == 1) and (isinstance(values[0], list) or isinstance(values[0], tuple)):
            values = values[0]
        l = len(values)
        if l > 4:
            raise TypeError("uniform vector has too-high order(%d)" % len(values))
        if any(isinstance(v, float) for v in values):
            if   l == 1: self.Uniform1f(location, values[0])
            elif l == 2: self.Uniform2f(location, values[0], values[1])
            elif l == 3: self.Uniform3f(location, values[0], values[1], values[2])
            else:        self.Uniform4f(location, values[0], values[1], values[2], values[3])
        else:
            if   l == 1: self.Uniform1i(location, values[0])
            elif l == 2: self.Uniform2i(location, values[0], values[1])
            elif l == 3: self.Uniform3i(location, values[0], values[1], values[2])
            else:        self.Uniform4i(location, values[0], values[1], values[2], values[3])

    ##### Convenience Functions #####

    def _init(self):
        self.enabled_attribs = set()

    def set_enabled_attribs(self, *attrs):
        want = set(attrs)
        for a in (want - self.enabled_attribs):
            self.EnableVertexAttribArray(a)
        for a in (self.enabled_attribs - want):
            self.DisableVertexAttribArray(a)
        self.enabled_attribs = want

    def set_texture(self, target=TEXTURE_2D, tex=0, tmu=0):
        self.ActiveTexture(self.TEXTURE0 + tmu)
        self.BindTexture(target, tex)

    def make_texture(self, target=TEXTURE_2D, wrap=CLAMP_TO_EDGE, filter=LINEAR_MIPMAP_NEAREST, img=None):
        tex = self.GenTextures()
        min_filter = filter
        if min_filter < self.NEAREST_MIPMAP_NEAREST:
            mag_filter = min_filter
        else:
            mag_filter = self.NEAREST + (min_filter & 1)
        self.BindTexture(target, tex)
        self.TexParameteri(target, self.TEXTURE_WRAP_S, wrap)
        self.TexParameteri(target, self.TEXTURE_WRAP_T, wrap)
        self.TexParameteri(target, self.TEXTURE_MIN_FILTER, min_filter)
        self.TexParameteri(target, self.TEXTURE_MAG_FILTER, mag_filter)
        if img:
            self.load_texture(target, img)
        return tex

    def load_texture(self, target, tex_or_img, img=None):
        if img:
            gl.BindTexture(target, tex_or_img)
        else:
            img = tex_or_img
        if   img.mode == 'RGBA': format = self.RGBA
        elif img.mode == 'RGB':  format = self.RGB
        elif img.mode == 'LA':   format = self.LUMINANCE_ALPHA
        elif img.mode == 'L':    format = self.LUMINANCE
        else: raise TypeError("image has unsupported color format '%s'" % img.mode)
        gl.TexImage2D(target, 0, format, img.size[0], img.size[1], 0, format, self.UNSIGNED_BYTE, img2str(img))

class GLShaderCompileError(SyntaxError):
    pass
class GLInvalidShaderError(GLShaderCompileError):
    pass

class GLShader(object):
    LOG_NEVER = 0
    LOG_ON_ERROR = 1
    LOG_IF_NOT_EMPTY = 2
    LOG_ALWAYS = 3
    LOG_DEFAULT = LOG_ON_ERROR

    def __init__(self, vs=None, fs=None, attributes=[], uniforms=[], loglevel=None):
        if not(vs): vs = self.vs
        if not(fs): fs = self.fs
        if not(attributes) and hasattr(self, 'attributes'):
            attributes = self.attributes
        if isinstance(attributes, dict):
            attributes = attributes.items()
        if not(uniforms) and hasattr(self, 'uniforms'):
            uniforms = self.uniforms
        if isinstance(uniforms, dict):
            uniforms = uniforms.items()
        uniforms = [((u, None) if isinstance(u, basestring) else u) for u in uniforms]
        if (loglevel is None) and hasattr(self, 'loglevel'):
            loglevel = self.loglevel
        if loglevel is None:
            loglevel = self.LOG_DEFAULT

        self.program = gl.CreateProgram()
        def handle_shader_log(status, log_getter, action):
            force_log = (loglevel >= self.LOG_ALWAYS) or ((loglevel >= self.LOG_ON_ERROR) and not(status))
            if force_log or (loglevel >= self.LOG_IF_NOT_EMPTY):
                log = log_getter().rstrip()
            else:
                log = "" 
            if force_log or ((loglevel >= self.LOG_IF_NOT_EMPTY) and log):
                if status:
                    print >>sys.stderr, "Info: log for %s %s:" % (self.__class__.__name__, action)
                else:
                    print >>sys.stderr, "Error: %s %s failed - log information follows:" % (self.__class__.__name__, action)
                for line in log.split('\n'):
                    print >>sys.stderr, '>', line.rstrip()
            if not status:
                raise GLShaderCompileError("failure during %s %s" % (self.__class__.__name__, action))
        def handle_shader(type_enum, type_name, src):
            if gl._is_desktop_gl:
                src = src.replace("highp ", "")
                src = src.replace("mediump ", "")
                src = src.replace("lowp ", "")
            shader = gl.CreateShader(type_enum)
            gl.ShaderSource(shader, src)
            gl.CompileShader(shader)
            handle_shader_log(gl.GetShaderi(shader, gl.COMPILE_STATUS),
                              lambda: gl.GetShaderInfoLog(shader),
                              type_name + " shader compilation")
            gl.AttachShader(self.program, shader)
        handle_shader(gl.VERTEX_SHADER, "vertex", vs)
        handle_shader(gl.FRAGMENT_SHADER, "fragment", fs)
        for attr in attributes:
            if not isinstance(attr, basestring):
                loc, name = attr
                if isinstance(loc, basestring):
                    loc, name = name, loc
                setattr(self, name, loc)
            elif hasattr(self, attr):
                name = attr
                loc = getattr(self, name)
            gl.BindAttribLocation(self.program, loc, name)
        gl.LinkProgram(self.program)
        handle_shader_log(gl.GetProgrami(self.program, gl.LINK_STATUS),
                          lambda: gl.GetProgramInfoLog(self.program),
                          "linking")
        gl.UseProgram(self.program)
        for name in attributes:
            if isinstance(name, basestring) and not(hasattr(self, attr)):
                setattr(self, name, int(gl.GetAttribLocation(self.program, name)))
        for u in uniforms:
            loc = int(gl.GetUniformLocation(self.program, u[0]))
            setattr(self, u[0], loc)
            if u[1] is not None:
                gl.Uniform(loc, *u[1:])

    def use(self):
        gl.UseProgram(self.program)
        return self

    @classmethod
    def get_instance(self):
        try:
            instance = self._instance
            if instance:
                return instance
            else:
                raise GLInvalidShaderError("shader failed to compile in the past")
        except AttributeError:
            try:
                self._instance = self()
            except GLShaderCompileError, e:
                self._instance = None
                raise
            return self._instance

# NOTE: OpenGL drawing code in Impressive uses the following conventions:
# - program binding is undefined
# - vertex attribute layout is undefined
# - vertex attribute enable/disable is managed by gl.set_enabled_attribs()
# - texture bindings are undefined
# - ActiveTexure is TEXTURE0
# - array and element array buffer bindings are undefined
# - BLEND is disabled, BlendFunc is (SRC_ALPHA, ONE_MINUS_SRC_ALPHA)
