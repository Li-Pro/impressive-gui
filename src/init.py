# import basic modules
import random, getopt, os, types, re, codecs, tempfile, glob, cStringIO, re
import traceback, subprocess, time, itertools, ctypes.util, zlib, urllib
from math import *
from ctypes import *

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
    _find_paths = [root, os.path.join(root, "win32"), os.path.join(root, "gs")] + filter(None, os.getenv("PATH").split(';'))
    def FindBinary(binary):
        if not binary.lower().endswith(".exe"):
            binary += ".exe"
        for p in _find_paths:
            path = os.path.join(p, binary)
            if os.path.isfile(path):
                return path
        return binary  # fall-back if not found
    pdftkPath = FindBinary("pdftk.exe")
    GhostScriptPlatformOptions = ["-I" + os.path.join(root, "gs")]
    try:
        import win32api
        HaveWin32API = True
        MPlayerPath = FindBinary("mplayer.exe")
        def RunURL(url):
            win32api.ShellExecute(0, "open", url, "", "", 0)
    except ImportError:
        HaveWin32API = False
        MPlayerPath = ""
        def RunURL(url): print "Error: cannot run URL `%s'" % url
    MPlayerPlatformOptions = [ "-colorkey", "0x000000" ]
    MPlayerColorKey = True
    if getattr(sys, "frozen", False):
        sys.path.append(root)
    FontPath = []
    FontList = ["Verdana.ttf", "Arial.ttf"]
    Nice = []
else:
    def FindBinary(x): return x
    GhostScriptPlatformOptions = []
    MPlayerPath = "mplayer"
    MPlayerPlatformOptions = [ "-vo", "gl" ]
    MPlayerColorKey = False
    pdftkPath = "pdftk"
    FontPath = ["/usr/share/fonts", "/usr/local/share/fonts", "/usr/X11R6/lib/X11/fonts/TTF"]
    FontList = ["DejaVuSans.ttf", "Vera.ttf", "Verdana.ttf"]
    Nice = ["nice", "-n", "7"]
    def RunURL(url):
        try:
            subprocess.Popen(["xdg-open", url])
        except OSError:
            print >>sys.stderr, "Error: cannot open URL `%s'" % url

# import special modules
try:
    import pygame
    from pygame.locals import *
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
    from PIL import TiffImagePlugin, BmpImagePlugin, JpegImagePlugin, PngImagePlugin, PpmImagePlugin
except (ValueError, ImportError), err:
    print >>sys.stderr, "Oops! Cannot load necessary modules:", err
    print >>sys.stderr, """To use Impressive, you need to install the following Python modules:
 - PyGame   [python-pygame]   http://www.pygame.org/
 - PIL      [python-imaging]  http://www.pythonware.com/products/pil/
   or Pillow                  http://pypi.python.org/pypi/Pillow/
 - PyWin32  (OPTIONAL, Win32) http://sourceforge.net/projects/pywin32/
Additionally, please be sure to have pdftoppm or GhostScript installed if you
intend to use PDF input."""
    sys.exit(1)

try:
    import thread
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
