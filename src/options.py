##### COMMAND-LINE PARSER AND HELP #############################################

def if_op(cond, res_then, res_else):
    if cond: return res_then
    else:    return res_else

def HelpExit(code=0):
    print """A nice presentation tool.

Usage: """+os.path.basename(sys.argv[0])+""" [OPTION...] <INPUT(S)...>

You may either play a PDF file, a directory containing image files or
individual image files.

Input options:
  -r,  --rotate <n>       rotate pages clockwise in 90-degree steps
       --scale            scale images to fit screen (not used in PDF mode)
       --supersample      use supersampling (only used in PDF mode)
  -s                      --supersample for PDF files, --scale for image files
  -I,  --script <path>    set the path of the info script
  -u,  --poll <seconds>   check periodically if the source file has been
                          updated and reload it if it did
  -X,  --shuffle          put input files into random order
  -h,  --help             show this help text and exit

Output options:
  -o,  --output <dir>     don't display the presentation, only render to .png
       --fullscreen       start in fullscreen mode
  -ff, --fake-fullscreen  start in "fake fullscreen" mode
  -f,  --windowed         start in windowed mode
  -g,  --geometry <WxH>   set window size or fullscreen resolution
  -A,  --aspect <X:Y>     adjust for a specific display aspect ratio (e.g. 5:4)
  -G,  --gamma <G[:BL]>   specify startup gamma and black level

Page options:
  -i,  --initialpage <n>  start with page <n>
  -p,  --pages <A-B>      only cache pages in the specified range;
                          implicitly sets -i <A>
  -w,  --wrap             go back to the first page after the last page
  -O,  --autooverview <x> automatically derive page visibility on overview page
                            -O first = show pages with captions
                            -O last  = show pages before pages with captions
  -Q,  --autoquit         quit after the last slide (no effect with --wrap)

Display options:
  -t,  --transition <trans[,trans2...]>
                          force a specific transitions or set of transitions
  -l,  --listtrans        print a list of available transitions and exit
  -F,  --font <file>      use a specific TrueType font file for the OSD
  -S,  --fontsize <px>    specify the OSD font size in pixels
  -C,  --cursor <F[:X,Y]> use a .png image as the mouse cursor
  -L,  --layout <spec>    set the OSD layout (please read the documentation)
  -z,  --zoom <factor>    set zoom factor (integer number, default: 2)
  -x,  --fade             fade in at start and fade out at end
       --spot-radius <px> set the initial radius of the spotlight, in pixels
       --invert           display slides in inverted colors
       --min-box-size <x> set minimum size of a highlight box, in pixels
       --darkness <p>     set highlight box mode darkness to <p> percent
       --noblur           use legacy blur implementation

Timing options:
  -M,  --minutes          display time in minutes, not seconds
       --clock            show current time instead of time elapsed
       --tracking         enable time tracking mode
  -a,  --auto <seconds>   automatically advance to next page after some seconds
  -d,  --duration <time>  set the desired duration of the presentation and show
                          a progress bar at the bottom of the screen
  -y,  --auto-auto        if a duration is set, set the default time-out so
                          that it will be reached exactly
  -k,  --auto-progress    shows a progress bar for each page for auto-advance
  -T,  --transtime <ms>   set transition duration in milliseconds
  -D,  --mousedelay <ms>  set mouse hide delay for fullscreen mode (in ms)
                          (0 = show permanently, 1 = don't show at all)
  -B,  --boxfade <ms>     set highlight box fade duration in milliseconds
  -Z,  --zoomtime <ms>    set zoom animation duration in milliseconds
  -q,  --page-progress    shows a progress bar based on the position in the
                          presentation (based on pages, not time)

Control options:
       --control-help     display help about control configuration and exit
  -e,  --bind             set controls (modify event/action bindings)
  -E,  --controls <file>  load control configuration from a file
       --noclicks         disable page navigation via left/right mouse click
  -W,  --nowheel          disable page navigation via mouse wheel
       --noquit           disable single-key shortcuts that quit the program
       --evtest           run Impressive in event test mode

Advanced options:
  -c,  --cache <mode>     set page cache mode:
                            -c none       = disable caching completely
                            -c memory     = store cache in RAM, uncompressed
                            -c compressed = store cache in RAM, compressed
                            -c disk       = store cache on disk temporarily
                            -c persistent = store cache on disk persistently
       --cachefile <path> set the persistent cache file path (implies -cp)
  -b,  --noback           don't pre-render images in the background
  -P,  --renderer <path>  set path to PDF renderer executable (GhostScript,
                          Xpdf/Poppler pdftoppm, or MuPDF mudraw/pdfdraw)
  -V,  --overscan <px>    render PDF files <px> pixels larger than the screen
       --nologo           disable startup logo and version number display
  -H,  --half-screen      show OSD on right half of the screen only
  -v,  --verbose          (slightly) more verbose operation

For detailed information, visit""", __website__
    sys.exit(code)

def ListTransitions():
    print "Available transitions:"
    standard = dict([(tc.__name__, None) for tc in AvailableTransitions])
    trans = [(tc.__name__, tc.__doc__) for tc in AllTransitions]
    trans.append(('None', "no transition"))
    trans.sort()
    maxlen = max([len(item[0]) for item in trans])
    for name, desc in trans:
        if name in standard:
            star = '*'
        else:
            star = ' '
        print star, name.ljust(maxlen), '-', desc
    print "(transitions with * are enabled by default)"
    sys.exit(0)

def TryTime(s, regexp, func):
    m = re.match(regexp, s, re.I)
    if not m: return 0
    return func(map(int, m.groups()))
def ParseTime(s):
    return TryTime(s, r'([0-9]+)s?$', lambda m: m[0]) \
        or TryTime(s, r'([0-9]+)m$', lambda m: m[0] * 60) \
        or TryTime(s, r'([0-9]+)[m:]([0-9]+)[ms]?$', lambda m: m[0] * 60 + m[1]) \
        or TryTime(s, r'([0-9]+)[h:]([0-9]+)[hm]?$', lambda m: m[0] * 3600 + m[1] * 60) \
        or TryTime(s, r'([0-9]+)[h:]([0-9]+)[m:]([0-9]+)s?$', lambda m: m[0] * 3600 + m[1] * 60 + m[2])

def opterr(msg, extra_lines=[]):
    print >>sys.stderr, "command line parse error:", msg
    for line in extra_lines:
        print >>sys.stderr, line
    print >>sys.stderr, "use `%s -h' to get help" % sys.argv[0]
    print >>sys.stderr, "or visit", __website__, "for full documentation"
    sys.exit(2)

def SetTransitions(list):
    global AvailableTransitions
    index = dict([(tc.__name__.lower(), tc) for tc in AllTransitions])
    index['none'] = None
    AvailableTransitions=[]
    for trans in list.split(','):
        try:
            AvailableTransitions.append(index[trans.lower()])
        except KeyError:
            opterr("unknown transition `%s'" % trans)

def ParseLayoutPosition(value):
    xpos = []
    ypos = []
    for c in value.strip().lower():
        if   c == 't': ypos.append(0)
        elif c == 'b': ypos.append(1)
        elif c == 'l': xpos.append(0)
        elif c == 'r': xpos.append(1)
        elif c == 'c': xpos.append(2)
        else: opterr("invalid position specification `%s'" % value)
    if not xpos: opterr("position `%s' lacks X component" % value)
    if not ypos: opterr("position `%s' lacks Y component" % value)
    if len(xpos)>1: opterr("position `%s' has multiple X components" % value)
    if len(ypos)>1: opterr("position `%s' has multiple Y components" % value)
    return (xpos[0] << 1) | ypos[0]
def SetLayoutSubSpec(key, value):
    global OSDTimePos, OSDTitlePos, OSDPagePos, OSDStatusPos
    global OSDAlpha, OSDMargin
    lkey = key.strip().lower()
    if lkey in ('a', 'alpha', 'opacity'):
        try:
            OSDAlpha = float(value)
        except ValueError:
            opterr("invalid alpha value `%s'" % value)
        if OSDAlpha > 1.0:
            OSDAlpha *= 0.01  # accept percentages, too
        if (OSDAlpha < 0.0) or (OSDAlpha > 1.0):
            opterr("alpha value %s out of range" % value)
    elif lkey in ('margin', 'dist', 'distance'):
        try:
            OSDMargin = float(value)
        except ValueError:
            opterr("invalid margin value `%s'" % value)
        if OSDMargin < 0:
            opterr("margin value %s out of range" % value)
    elif lkey in ('t', 'time'):
        OSDTimePos = ParseLayoutPosition(value)
    elif lkey in ('title', 'caption'):
        OSDTitlePos = ParseLayoutPosition(value)
    elif lkey in ('page', 'number'):
        OSDPagePos = ParseLayoutPosition(value)
    elif lkey in ('status', 'info'):
        OSDStatusPos = ParseLayoutPosition(value)
    else:
        opterr("unknown layout element `%s'" % key)
def SetLayout(spec):
    for sub in spec.replace(':', '=').split(','):
        try:
            key, value = sub.split('=')
        except ValueError:
            opterr("invalid layout spec `%s'" % sub)
        SetLayoutSubSpec(key, value)

def ParseCacheMode(arg):
    arg = arg.strip().lower()
    if "none".startswith(arg): return NoCache
    if "off".startswith(arg): return NoCache
    if "memory".startswith(arg): return MemCache
    if arg == 'z': return CompressedCache
    if "compressed".startswith(arg): return CompressedCache
    if "disk".startswith(arg): return FileCache
    if "file".startswith(arg): return FileCache
    if "persistent".startswith(arg): return PersistentCache
    opterr("invalid cache mode `%s'" % arg)

def ParseAutoOverview(arg):
    arg = arg.strip().lower()
    if "off".startswith(arg): return Off
    if "first".startswith(arg): return First
    if "last".startswith(arg): return Last
    try:
        i = int(arg)
        assert (i >= Off) and (i <= Last)
    except:
        opterr("invalid auto-overview mode `%s'" % arg)

def ParseOptions(argv):
    global FileName, FileList, Fullscreen, Scaling, Supersample, CacheMode
    global TransitionDuration, MouseHideDelay, BoxFadeDuration, ZoomDuration
    global ScreenWidth, ScreenHeight, InitialPage, Wrap, TimeTracking
    global AutoAdvance, RenderToDirectory, Rotation, DAR, Verbose
    global BackgroundRendering, UseAutoScreenSize, PollInterval, CacheFileName
    global PageRangeStart, PageRangeEnd, FontList, FontSize, Gamma, BlackLevel
    global EstimatedDuration, CursorImage, CursorHotspot, MinutesOnly, Overscan
    global PDFRendererPath, InfoScriptPath, EventTestMode
    global AutoOverview, ZoomFactor, FadeInOut, ShowLogo, Shuffle, PageProgress
    global QuitAtEnd, ShowClock, HalfScreen, SpotRadius, InvertPages
    global MinBoxSize, AutoAutoAdvance, AutoAdvanceProgress, BoxFadeDarkness
    global WindowPos, FakeFullscreen, UseBlurShader
    DefaultControls = True

    try:  # unused short options: jnJKNRUY
        opts, args = getopt.getopt(argv, \
            "vhfg:sc:i:wa:t:lo:r:T:D:B:Z:P:A:mbp:u:F:S:G:d:C:ML:I:O:z:xXqV:QHykWe:E:", \
           ["help", "fullscreen", "geometry=", "scale", "supersample", \
            "nocache", "initialpage=", "wrap", "auto=", "listtrans", "output=", \
            "rotate=", "transition=", "transtime=", "mousedelay=", "boxfade=", \
            "zoom=", "gspath=", "renderer=", "aspect=", "memcache", \
            "noback", "pages=", "poll=", "font=", "fontsize=", "gamma=",
            "duration=", "cursor=", "minutes", "layout=", "script=", "cache=",
            "cachefile=", "autooverview=", "zoomtime=", "fade", "nologo",
            "shuffle", "page-progress", "overscan=", "autoquit", "noclicks",
            "clock", "half-screen", "spot-radius=", "invert", "min-box-size=",
            "auto-auto", "auto-progress", "darkness=", "no-clicks", "nowheel",
            "no-wheel", "fake-fullscreen", "windowed", "verbose", "noblur",
            "tracking", "bind=", "controls=", "control-help", "evtest",
            "noquit"])
    except getopt.GetoptError, message:
        opterr(message)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            HelpExit()
        if opt in ("-l", "--listtrans"):
            ListTransitions()
        if opt in ("-v", "--verbose"):
            Verbose = not(Verbose)
        if opt == "--fullscreen":      Fullscreen, FakeFullscreen = True,  False
        if opt == "--fake-fullscreen": Fullscreen, FakeFullscreen = True,  True
        if opt == "--windowed":        Fullscreen, FakeFullscreen = False, False
        if opt == "-f":
            if FakeFullscreen: Fullscreen, FakeFullscreen = True,  False
            elif   Fullscreen: Fullscreen, FakeFullscreen = False, False
            else:              Fullscreen, FakeFullscreen = True,  True
        if opt in ("-s", "--scale"):
            Scaling = not(Scaling)
        if opt in ("-s", "--supersample"):
            Supersample = 2
        if opt in ("-w", "--wrap"):
            Wrap = not(Wrap)
        if opt in ("-x", "--fade"):
            FadeInOut = not(FadeInOut)
        if opt in ("-O", "--autooverview"):
            AutoOverview = ParseAutoOverview(arg)
        if opt in ("-c", "--cache"):
            CacheMode = ParseCacheMode(arg)
        if opt == "--nocache":
            print >>sys.stderr, "Note: The `--nocache' option is deprecated, use `--cache none' instead."
            CacheMode = NoCache
        if opt in ("-m", "--memcache"):
            print >>sys.stderr, "Note: The `--memcache' option is deprecated, use `--cache memory' instead."
            CacheMode = MemCache
        if opt == "--cachefile":
            CacheFileName = arg
            CacheMode = PersistentCache
        if opt in ("-M", "--minutes"):
            MinutesOnly = not(MinutesOnly)
        if opt in ("-b", "--noback"):
            BackgroundRendering = not(BackgroundRendering)
        if opt in ("-t", "--transition"):
            SetTransitions(arg)
        if opt in ("-L", "--layout"):
            SetLayout(arg)
        if opt in ("-o", "--output"):
            RenderToDirectory = arg
        if opt in ("-I", "--script"):
            InfoScriptPath = arg
        if opt in ("-F", "--font"):
            FontList = [arg]
        if opt == "--nologo":
            ShowLogo = not(ShowLogo)
        if opt in ("--noclicks", "--no-clicks"):
            if not DefaultControls:
                print >>sys.stderr, "Note: The default control settings have been modified, the `--noclicks' option might not work as expected."
            BindEvent("lmb, rmb, ctrl+lmb, ctrl+rmb -= goto-next, goto-prev, goto-next-notrans, goto-prev-notrans")
        if opt in ("-W", "--nowheel", "--no-wheel"):
            if not DefaultControls:
                print >>sys.stderr, "Note: The default control settings have been modified, the `--nowheel' option might not work as expected."
            BindEvent("wheelup, wheeldown, ctrl+wheelup, ctrl+wheeldown -= goto-next, goto-prev, goto-next-notrans, goto-prev-notrans, overview-next, overview-prev")
        if opt in ("--noquit", "--no-quit"):
            if not DefaultControls:
                print >>sys.stderr, "Note: The default control settings have been modified, the `--nowheel' option might not work as expected."
            BindEvent("q,escape -= quit")            
        if opt in ("-e", "--bind"):
            BindEvent(arg, error_prefix="--bind")
            DefaultControls = False
        if opt in ("-E", "--controls"):
            ParseInputBindingFile(arg)
            DefaultControls = False
        if opt == "--control-help":
            EventHelp()
            sys.exit(0)
        if opt == "--evtest":
            EventTestMode = not(EventTestMode)
        if opt == "--clock":
            ShowClock = not(ShowClock)
        if opt == "--tracking":
            TimeTracking = not(TimeTracking)
        if opt in ("-X", "--shuffle"):
            Shuffle = not(Shuffle)
        if opt in ("-Q", "--autoquit"):
            QuitAtEnd = not(QuitAtEnd)
        if opt in ("-y", "--auto-auto"):
            AutoAutoAdvance = not(AutoAutoAdvance)
        if opt in ("-k", "--auto-progress"):
            AutoAdvanceProgress = not(AutoAdvanceProgress)
        if opt in ("-q", "--page-progress"):
            PageProgress = not(PageProgress)
        if opt in ("-H", "--half-screen"):
            HalfScreen = not(HalfScreen)
            if HalfScreen:
                ZoomDuration = 0
        if opt == "--invert":
            InvertPages = not(InvertPages)
        if opt in ("-P", "--gspath", "--renderer"):
            if any(r.supports(arg) for r in AvailableRenderers):
                PDFRendererPath = arg
            else:
                opterr("unrecognized --renderer",
                    ["supported renderer binaries are:"] +
                    ["- %s (%s)" % (", ".join(r.binaries), r.name) for r in AvailableRenderers])
        if opt in ("-S", "--fontsize"):
            try:
                FontSize = int(arg)
                assert FontSize > 0
            except:
                opterr("invalid parameter for --fontsize")
        if opt in ("-i", "--initialpage"):
            try:
                InitialPage = int(arg)
                assert InitialPage > 0
            except:
                opterr("invalid parameter for --initialpage")
        if opt in ("-d", "--duration"):
            try:
                EstimatedDuration = ParseTime(arg)
                assert EstimatedDuration > 0
            except:
                opterr("invalid parameter for --duration")
        if opt in ("-a", "--auto"):
            try:
                AutoAdvance = int(float(arg) * 1000)
                assert (AutoAdvance > 0) and (AutoAdvance <= 86400000)
            except:
                opterr("invalid parameter for --auto")
        if opt in ("-T", "--transtime"):
            try:
                TransitionDuration = int(arg)
                assert (TransitionDuration >= 0) and (TransitionDuration < 32768)
            except:
                opterr("invalid parameter for --transtime")
        if opt in ("-D", "--mousedelay"):
            try:
                MouseHideDelay = int(arg)
                assert (MouseHideDelay >= 0) and (MouseHideDelay < 32768)
            except:
                opterr("invalid parameter for --mousedelay")
        if opt in ("-B", "--boxfade"):
            try:
                BoxFadeDuration = int(arg)
                assert (BoxFadeDuration >= 0) and (BoxFadeDuration < 32768)
            except:
                opterr("invalid parameter for --boxfade")
        if opt in ("-Z", "--zoomtime"):
            try:
                ZoomDuration = int(arg)
                assert (ZoomDuration >= 0) and (ZoomDuration < 32768)
            except:
                opterr("invalid parameter for --zoomtime")
        if opt == "--spot-radius":
            try:
                SpotRadius = int(arg)
            except:
                opterr("invalid parameter for --spot-radius")
        if opt == "--min-box-size":
            try:
                MinBoxSize = int(arg)
            except:
                opterr("invalid parameter for --min-box-size")
        if opt in ("-r", "--rotate"):
            try:
                Rotation = int(arg)
            except:
                opterr("invalid parameter for --rotate")
            while Rotation < 0: Rotation += 4
            Rotation = Rotation & 3
        if opt in ("-u", "--poll"):
            try:
                PollInterval = int(arg)
                assert PollInterval >= 0
            except:
                opterr("invalid parameter for --poll")
        if opt in ("-g", "--geometry"):
            try:
                parts = arg.replace('+', '|+').replace('-', '|-').split('|')
                assert len(parts) in (1, 3)
                if len(parts) == 3:
                    WindowPos = (int(parts[1]), int(parts[2]))
                else:
                    assert len(parts) == 1
                ScreenWidth, ScreenHeight = map(int, parts[0].split("x"))
                assert (ScreenWidth  >= 320) and (ScreenWidth  < 32768)
                assert (ScreenHeight >= 200) and (ScreenHeight < 32768)
                UseAutoScreenSize = False
            except:
                opterr("invalid parameter for --geometry")
        if opt in ("-p", "--pages"):
            try:
                PageRangeStart, PageRangeEnd = map(int, arg.split("-"))
                assert PageRangeStart > 0
                assert PageRangeStart <= PageRangeEnd
            except:
                opterr("invalid parameter for --pages")
            InitialPage = PageRangeStart
        if opt in ("-A", "--aspect"):
            try:
                if ':' in arg:
                    fx, fy = map(float, arg.split(':'))
                    DAR = fx / fy
                else:
                    DAR = float(arg)
                assert DAR > 0.0
            except:
                opterr("invalid parameter for --aspect")
        if opt in ("-G", "--gamma"):
            try:
                if ':' in arg:
                    arg, bl = arg.split(':', 1)
                    BlackLevel = int(bl)
                Gamma = float(arg)
                assert Gamma > 0.0
                assert (BlackLevel >= 0) and (BlackLevel < 255)
            except:
                opterr("invalid parameter for --gamma")
        if opt in ("-C", "--cursor"):
            try:
                if ':' in arg:
                    arg = arg.split(':')
                    assert len(arg) > 1
                    CursorImage = ':'.join(arg[:-1])
                    CursorHotspot = map(int, arg[-1].split(','))
                else:
                    CursorImage = arg
                assert (BlackLevel >= 0) and (BlackLevel < 255)
            except:
                opterr("invalid parameter for --cursor")
        if opt in ("-z", "--zoom"):
            try:
                ZoomFactor = int(arg)
                assert ZoomFactor > 1
            except:
                opterr("invalid parameter for --zoom")
        if opt in ("-V", "--overscan"):
            try:
                Overscan = int(arg)
            except:
                opterr("invalid parameter for --overscan")
        if opt == "--darkness":
            try:
                BoxFadeDarkness = float(arg) * 0.01
            except:
                opterr("invalid parameter for --darkness")
        if opt == "--noblur":
            UseBlurShader = not(UseBlurShader)

    for arg in args:
        AddFile(arg)
    if not(FileList) and not(EventTestMode):
        opterr("no playable files specified")
