# import basic modules
import random, getopt, os, types, re, codecs, tempfile, glob, StringIO, re
import traceback, subprocess, time
from math import *

# import hashlib for MD5 generation, but fall back to old md5 lib if unavailable
# (this is the case for Python versions older than 2.5)
try:
    import hashlib
    md5obj = hashlib.md5
except ImportError:
    import md5
    md5obj = md5.new

# initialize some platform-specific settings
if os.name == "nt":
    root = os.path.split(sys.argv[0])[0] or "."
    pdftoppmPath = os.path.join(root, "pdftoppm.exe")
    GhostScriptPath = os.path.join(root, "gs\\gswin32c.exe")
    GhostScriptPlatformOptions = ["-I" + os.path.join(root, "gs")]
    try:
        import win32api
        MPlayerPath = os.path.join(root, "mplayer.exe")
        def GetScreenSize():
            dm = win32api.EnumDisplaySettings(None, -1) #ENUM_CURRENT_SETTINGS
            return (int(dm.PelsWidth), int(dm.PelsHeight))
        def RunURL(url):
            win32api.ShellExecute(0, "open", url, "", "", 0)
    except ImportError:
        MPlayerPath = ""
        def GetScreenSize(): return pygame.display.list_modes()[0]
        def RunURL(url): print "Error: cannot run URL `%s'" % url
    MPlayerPlatformOptions = [ "-colorkey", "0x000000" ]
    MPlayerColorKey = True
    pdftkPath = os.path.join(root, "pdftk.exe")
    FileNameEscape = '"'
    spawn = os.spawnv
    if getattr(sys, "frozen", None):
        sys.path.append(root)
    FontPath = []
    FontList = ["Verdana.ttf", "Arial.ttf"]
else:
    pdftoppmPath = "pdftoppm"
    GhostScriptPath = "gs"
    GhostScriptPlatformOptions = []
    MPlayerPath = "mplayer"
    MPlayerPlatformOptions = [ "-vo", "gl" ]
    MPlayerColorKey = False
    pdftkPath = "pdftk"
    spawn = os.spawnvp
    FileNameEscape = ""
    FontPath = ["/usr/share/fonts", "/usr/local/share/fonts", "/usr/X11R6/lib/X11/fonts/TTF"]
    FontList = ["DejaVuSans.ttf", "Vera.ttf", "Verdana.ttf"]
    def RunURL(url):
        try:
            spawn(os.P_NOWAIT, "xdg-open", ["xdg-open", url])
        except OSError:
            print >>sys.stderr, "Error: cannot open URL `%s'" % url
    def GetScreenSize():
        res_re = re.compile(r'\s*(\d+)x(\d+)\s+\d+\.\d+\*')
        for path in os.getenv("PATH").split(':'):
            fullpath = os.path.join(path, "xrandr")
            if os.path.exists(fullpath):
                res = None
                try:
                    for line in os.popen(fullpath, "r"):
                        m = res_re.match(line)
                        if m:
                            res = tuple(map(int, m.groups()))
                except OSError:
                    pass
                if res:
                    return res
        return pygame.display.list_modes()[0]

# import special modules
try:
    from OpenGL.GL import *
    import pygame
    from pygame.locals import *
    import Image, ImageDraw, ImageFont, ImageFilter
    import TiffImagePlugin, BmpImagePlugin, JpegImagePlugin, PngImagePlugin, PpmImagePlugin
except (ValueError, ImportError), err:
    print >>sys.stderr, "Oops! Cannot load necessary modules:", err
    print >>sys.stderr, """To use Impressive, you need to install the following Python modules:
 - PyOpenGL [python-opengl]   http://pyopengl.sourceforge.net/
 - PyGame   [python-pygame]   http://www.pygame.org/
 - PIL      [python-imaging]  http://www.pythonware.com/products/pil/
 - PyWin32  (OPTIONAL, Win32) http://starship.python.net/crew/mhammond/win32/
Additionally, please be sure to have pdftoppm or GhostScript installed if you
intend to use PDF input."""
    sys.exit(1)

try:
    import thread
    EnableBackgroundRendering = True
    def create_lock(): return thread.allocate_lock()
except ImportError:
    EnableBackgroundRendering = False
    class pseudolock:
        def __init__(self): self.state = False
        def acquire(self, dummy=0): self.state = True
        def release(self): self.state = False
        def locked(self): return self.state
    def create_lock(): return pseudolock()
