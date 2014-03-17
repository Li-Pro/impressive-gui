##### OSD FONT RENDERER ########################################################

# force a string or sequence of ordinals into a unicode string
def ForceUnicode(s, charset='iso8859-15'):
    if type(s) == types.UnicodeType:
        return s
    if type(s) == types.StringType:
        return unicode(s, charset, 'ignore')
    if type(s) in (types.TupleType, types.ListType):
        return u''.join(map(unichr, s))
    raise TypeError, "string argument not convertible to Unicode"

# search a system font path for a font file
def SearchFont(root, name):
    if not os.path.isdir(root):
        return None
    infix = ""
    fontfile = []
    while (len(infix) < 10) and (len(fontfile) != 1):
        fontfile = filter(os.path.isfile, glob.glob(root + infix + name))
        infix += "*/"
    if len(fontfile) != 1:
        return None
    else:
        return fontfile[0]

# load a system font
def LoadFont(dirs, name, size):
    # first try to load the font directly
    try:
        return ImageFont.truetype(name, size, encoding='unic')
    except:
        pass
    # no need to search further on Windows
    if os.name == 'nt':
        return None
    # start search for the font
    for dir in dirs:
        fontfile = SearchFont(dir + "/", name)
        if fontfile:
            try:
                return ImageFont.truetype(fontfile, size, encoding='unic')
            except:
                pass
    return None

# alignment constants
Left = 0
Right = 1
Center = 2
Down = 0
Up = 1
Auto = -1

# font renderer class
class GLFont:
    def __init__(self, width, height, name, size, search_path=[], default_charset='iso8859-15', extend=1, blur=1):
        self.width = width
        self.height = height
        self._i_extend = range(extend)
        self._i_blur = range(blur)
        self.feather = extend + blur + 1
        self.current_x = 0
        self.current_y = 0
        self.max_height = 0
        self.boxes = {}
        self.widths = {}
        self.line_height = 0
        self.default_charset = default_charset
        if type(name) == types.StringType:
            self.font = LoadFont(search_path, name, size)
        else:
            for check_name in name:
                self.font = LoadFont(search_path, check_name, size)
                if self.font: break
        if not self.font:
            raise IOError, "font file not found"
        self.img = Image.new('LA', (width, height))
        self.alpha = Image.new('L', (width, height))
        self.extend = ImageFilter.MaxFilter()
        self.blur = ImageFilter.Kernel((3, 3), [1,2,1,2,4,2,1,2,1])
        self.tex = gl.make_texture(gl.TEXTURE_2D, filter=gl.NEAREST)
        self.AddString(range(32, 128))
        self.vertices = None
        self.index_buffer = None
        self.index_buffer_capacity = 0

    def AddCharacter(self, c):
        w, h = self.font.getsize(c)
        try:
            ox, oy = self.font.getoffset(c)
            w += ox
            h += oy
        except AttributeError:
            pass
        self.line_height = max(self.line_height, h)
        size = (w + 2 * self.feather, h + 2 * self.feather)
        glyph = Image.new('L', size)
        draw = ImageDraw.Draw(glyph)
        draw.text((self.feather, self.feather), c, font=self.font, fill=255)
        del draw

        box = self.AllocateGlyphBox(*size)
        self.img.paste(glyph, (box.orig_x, box.orig_y))

        for i in self._i_extend: glyph = glyph.filter(self.extend)
        for i in self._i_blur:   glyph = glyph.filter(self.blur)
        self.alpha.paste(glyph, (box.orig_x, box.orig_y))

        self.boxes[c] = box
        self.widths[c] = w
        del glyph

    def AddString(self, s, charset=None, fail_silently=False):
        update_count = 0
        try:
            for c in ForceUnicode(s, self.GetCharset(charset)):
                if c in self.widths:
                    continue
                self.AddCharacter(c)
                update_count += 1
        except ValueError:
            if fail_silently:
                pass
            else:
                raise
        if not update_count: return
        self.img.putalpha(self.alpha)
        gl.load_texture(gl.TEXTURE_2D, self.tex, self.img)

    def AllocateGlyphBox(self, w, h):
        if self.current_x + w > self.width:
            self.current_x = 0
            self.current_y += self.max_height
            self.max_height = 0
        if self.current_y + h > self.height:
            raise ValueError, "bitmap too small for all the glyphs"
        box = self.GlyphBox()
        box.orig_x = self.current_x
        box.orig_y = self.current_y
        box.size_x = w
        box.size_y = h
        box.x0 =  self.current_x      / float(self.width)
        box.y0 =  self.current_y      / float(self.height)
        box.x1 = (self.current_x + w) / float(self.width)
        box.y1 = (self.current_y + h) / float(self.height)
        box.dsx = w * PixelX
        box.dsy = h * PixelY
        self.current_x += w
        self.max_height = max(self.max_height, h)
        return box

    def GetCharset(self, charset=None):
        if charset: return charset
        return self.default_charset

    def SplitText(self, s, charset=None):
        return ForceUnicode(s, self.GetCharset(charset)).split(u'\n')

    def GetLineHeight(self):
        return self.line_height

    def GetTextWidth(self, s, charset=None):
        return max([self.GetTextWidthEx(line) for line in self.SplitText(s, charset)])

    def GetTextHeight(self, s, charset=None):
        return len(self.SplitText(s, charset)) * self.line_height

    def GetTextSize(self, s, charset=None):
        lines = self.SplitText(s, charset)
        return (max([self.GetTextWidthEx(line) for line in lines]), len(lines) * self.line_height)

    def GetTextWidthEx(self, u):
        if u: return sum([self.widths.get(c, 0) for c in u])
        else: return 0

    def GetTextHeightEx(self, u=[]):
        return self.line_height

    def AlignTextEx(self, x, u, align=Left):
        if not align: return x
        return x - (self.GetTextWidthEx(u) / align)

    class FontShader(GLShader):
        vs = """
            attribute highp vec4 aPosAndTexCoord;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_Position = vec4(vec2(-1.0, 1.0) + aPosAndTexCoord.xy * vec2(2.0, -2.0), 0.0, 1.0);
                vTexCoord = aPosAndTexCoord.zw;
            }
        """
        fs = """
            uniform lowp sampler2D uTex;
            uniform lowp vec4 uColor;
            varying mediump vec2 vTexCoord;
            void main() {
                gl_FragColor = uColor * texture2D(uTex, vTexCoord);
            }
        """
        attributes = { 0: 'aPosAndTexCoord' }
        uniforms = ['uColor']

    def BeginDraw(self):
        self.vertices = []

    def EndDraw(self, color=(1.0, 1.0, 1.0), alpha=1.0, beveled=True):
        if not self.vertices:
            self.vertices = None
            return
        char_count = len(self.vertices) / 16
        if char_count > 16383:
            print >>sys.stderr, "Internal Error: too many characters (%d) to display in one go, truncating." % char_count
            char_count = 16383

        # create an index buffer large enough for the text
        if not(self.index_buffer) or (self.index_buffer_capacity < char_count):
            self.index_buffer_capacity = (char_count + 63) & (~63)
            data = []
            for b in xrange(0, self.index_buffer_capacity * 4, 4):
                data.extend([b+0, b+2, b+1, b+1, b+2, b+3])
            if not self.index_buffer:
                self.index_buffer = gl.GenBuffers()
            gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.index_buffer)
            gl.BufferData(gl.ELEMENT_ARRAY_BUFFER, data=data, type=gl.UNSIGNED_SHORT, usage=gl.DYNAMIC_DRAW)
        else:
            gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.index_buffer)

        # set the vertex buffer
        vbuf = (c_float * len(self.vertices))(*self.vertices)
        gl.BindBuffer(gl.ARRAY_BUFFER, 0)
        gl.set_enabled_attribs(0)
        gl.VertexAttribPointer(0, 4, gl.FLOAT, False, 0, vbuf)

        # draw it
        shader = self.FontShader.get_instance().use()
        gl.BindTexture(gl.TEXTURE_2D, self.tex)
        if beveled:
            gl.BlendFunc(gl.ZERO, gl.ONE_MINUS_SRC_ALPHA)
            gl.Uniform4f(shader.uColor, 0.0, 0.0, 0.0, alpha)
            gl.DrawElements(gl.TRIANGLES, char_count * 6, gl.UNSIGNED_SHORT, 0)
        gl.BlendFunc(gl.ONE, gl.ONE)
        gl.Uniform4f(shader.uColor, color[0] * alpha, color[1] * alpha, color[2] * alpha, 1.0)
        gl.DrawElements(gl.TRIANGLES, char_count * 6, gl.UNSIGNED_SHORT, 0)
        gl.BlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
        self.vertices = None

    def Draw(self, origin, text, charset=None, align=Left, color=(1.0, 1.0, 1.0), alpha=1.0, beveled=True, bold=False):
        own_draw = (self.vertices is None)
        if own_draw:
            self.BeginDraw()
        lines = self.SplitText(text, charset)
        x0, y = origin
        x0 -= self.feather
        y -= self.feather
        for line in lines:
            sy = y * PixelY
            x = self.AlignTextEx(x0, line, align)
            for c in line:
                if not c in self.widths: continue
                self.boxes[c].add_vertices(self.vertices, x * PixelX, sy)
                x += self.widths[c]
            y += self.line_height
        if bold and not(beveled):
            self.Draw((origin[0] + 1, origin[1]), text, charset=charset, align=align, color=color, alpha=alpha, beveled=False, bold=False)
        if own_draw:
            self.EndDraw(color, alpha, beveled)

    class GlyphBox:
        def add_vertices(self, vertex_list, sx=0.0, sy=0.0):
            vertex_list.extend([
                sx,            sy,            self.x0, self.y0,
                sx + self.dsx, sy,            self.x1, self.y0,
                sx,            sy + self.dsy, self.x0, self.y1,
                sx + self.dsx, sy + self.dsy, self.x1, self.y1,
            ])

# high-level draw function
def DrawOSD(x, y, text, halign=Auto, valign=Auto, alpha=1.0):
    if not(OSDFont) or not(text) or (alpha <= 0.004): return
    if alpha > 1.0: alpha = 1.0
    if halign == Auto:
        if x < 0:
            x += ScreenWidth
            halign = Right
        else:
            halign = Left
    if HalfScreen and (halign == Left):
        x += ScreenWidth / 2
    if valign == Auto:
        if y < 0:
            y += ScreenHeight
            valign = Up
        else:
            valign = Down
        if valign != Down:
            y -= OSDFont.GetLineHeight() / valign
    OSDFont.Draw((x, y), text, align=halign, alpha=alpha)

# very high-level draw function
def DrawOSDEx(position, text, alpha_factor=1.0):
    xpos = position >> 1
    y = (1 - 2 * (position & 1)) * OSDMargin
    if xpos < 2:
        x = (1 - 2 * xpos) * OSDMargin
        halign = Auto
    else:
        x = ScreenWidth / 2
        halign = Center
    DrawOSD(x, y, text, halign, alpha = OSDAlpha * alpha_factor)

RequiredShaders.append(GLFont.FontShader)
