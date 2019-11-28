# import basic modules
import random, getopt, os, re, codecs, tempfile, glob, io, re, hashlib
import traceback, subprocess, time, itertools, ctypes.util, zlib, urllib
from math import *
from ctypes import *

# initialize some platform-specific settings
if os.name == "nt":
    root = os.path.split(sys.argv[0])[0] or "."
    _find_paths = [root, os.path.join(root, "win32"), os.path.join(root, "gs")] + list(filter(None, os.getenv("PATH").split(';')))
    def FindBinary(binary):
        if not binary.lower().endswith(".exe"):
            binary += ".exe"
        for p in _find_paths:
            path = os.path.join(p, binary)
            if os.path.isfile(path):
                return os.path.abspath(path)
        return binary  # fall-back if not found
    pdftkPath = FindBinary("pdftk.exe")
    mutoolPath = FindBinary("mutool.exe")
    ffmpegPath = FindBinary("ffmpeg.exe")
    GhostScriptPlatformOptions = ["-I" + os.path.join(root, "gs")]
    try:
        import win32api, win32gui
        HaveWin32API = True
        MPlayerPath = FindBinary("mplayer.exe")
        def RunURL(url):
            win32api.ShellExecute(0, "open", url, "", "", 0)
    except ImportError:
        HaveWin32API = False
        MPlayerPath = ""
        def RunURL(url): print("Error: cannot run URL `%s'" % url)
    if getattr(sys, "frozen", False):
        sys.path.append(root)
    FontPath = []
    FontList = ["verdana.ttf", "arial.ttf"]
    Nice = []
else:
    def FindBinary(x): return x
    GhostScriptPlatformOptions = []
    MPlayerPath = "mplayer"
    pdftkPath = "pdftk"
    mutoolPath = "mutool"
    ffmpegPath = "ffmpeg"
    FontPath = ["/usr/share/fonts", "/usr/local/share/fonts", "/usr/X11R6/lib/X11/fonts/TTF"]
    FontList = ["DejaVuSans.ttf", "Vera.ttf", "Verdana.ttf"]
    Nice = ["nice", "-n", "7"]
    def RunURL(url):
        try:
            Popen(["xdg-open", url])
        except OSError:
            print("Error: cannot open URL `%s'" % url, file=sys.stderr)

# import special modules
try:
    import pygame
    from pygame.locals import *
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
    from PIL import TiffImagePlugin, BmpImagePlugin, JpegImagePlugin, PngImagePlugin, PpmImagePlugin
except (ValueError, ImportError) as err:
    print("Oops! Cannot load necessary modules:", err, file=sys.stderr)
    print("""To use Impressive, you need to install the following Python modules:
 - PyGame   [python-pygame]   http://www.pygame.org/
 - PIL      [python-imaging]  http://www.pythonware.com/products/pil/
   or Pillow                  http://pypi.python.org/pypi/Pillow/
 - PyWin32  (OPTIONAL, Win32) http://sourceforge.net/projects/pywin32/
Additionally, please be sure to have mupdf-tools and pdftk installed if you
intend to use PDF input.""", file=sys.stderr)
    sys.exit(1)

# Python 2/3 compatibility fixes
try:  # Python 2 path
    basestring  # only exists in Python 2
    def Popen(cmdline, *args, **kwargs):
        # Python 2's subprocess.Popen needs manual unicode->str conversion
        enc = sys.getfilesystemencoding()
        cmdline = [arg.encode(enc, 'replace') for arg in cmdline]
        return subprocess.Popen(cmdline, *args, **kwargs)
except:  # Python 3 path
    basestring = str
    Popen = subprocess.Popen
    raw_input = input

try:
    try:
        import thread
    except ImportError:
        import _thread as thread
    HaveThreads = True
    def create_lock(): return thread.allocate_lock()
    def get_thread_id(): return thread.get_ident()
except ImportError:
    HaveThreads = False
    class pseudolock:
        def __init__(self): self.state = False
        def acquire(self, dummy=0): self.state = True
        def release(self): self.state = False
        def locked(self): return self.state
    def create_lock(): return pseudolock()
    def get_thread_id(): return 0xDEADC0DE

CleanExit = False
