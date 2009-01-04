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
        self.tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        self.AddString(range(32, 128))

    def AddCharacter(self, c):
        w, h = self.font.getsize(c)
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
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE_ALPHA, \
                     self.width, self.height, 0, \
                     GL_LUMINANCE_ALPHA, GL_UNSIGNED_BYTE, self.img.tostring())

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

    def Draw(self, origin, text, charset=None, align=Left, color=(1.0, 1.0, 1.0), alpha=1.0, beveled=True):
        lines = self.SplitText(text, charset)
        x0, y0 = origin
        x0 -= self.feather
        y0 -= self.feather
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        if beveled:
            glBlendFunc(GL_ZERO, GL_ONE_MINUS_SRC_ALPHA)
            glColor4d(0.0, 0.0, 0.0, alpha)
            self.DrawLinesEx(x0, y0, lines, align)
        glBlendFunc(GL_ONE, GL_ONE)
        glColor3d(color[0] * alpha, color[1] * alpha, color[2] * alpha)
        self.DrawLinesEx(x0, y0, lines, align)
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

    def DrawLinesEx(self, x0, y, lines, align=Left):
        global PixelX, PixelY
        glBegin(GL_QUADS)
        for line in lines:
            sy = y * PixelY
            x = self.AlignTextEx(x0, line, align)
            for c in line:
                if not c in self.widths: continue
                self.boxes[c].render(x * PixelX, sy)
                x += self.widths[c]
            y += self.line_height
        glEnd()

    class GlyphBox:
        def render(self, sx=0.0, sy=0.0):
            glTexCoord2d(self.x0, self.y0); glVertex2d(sx,          sy)
            glTexCoord2d(self.x0, self.y1); glVertex2d(sx,          sy+self.dsy)
            glTexCoord2d(self.x1, self.y1); glVertex2d(sx+self.dsx, sy+self.dsy)
            glTexCoord2d(self.x1, self.y0); glVertex2d(sx+self.dsx, sy)

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
    if valign == Auto:
        if y < 0:
            y += ScreenHeight
            valign = Up
        else:
            valign = Down
        if valign != Down:
            y -= OSDFont.GetLineHeight() / valign
    if TextureTarget != GL_TEXTURE_2D:
        glDisable(TextureTarget)
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
