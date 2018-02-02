##### TOOL CODE ################################################################

# read and write the PageProps and FileProps meta-dictionaries
def GetProp(prop_dict, key, prop, default=None):
    if not key in prop_dict: return default
    if type(prop) == types.StringType:
        return prop_dict[key].get(prop, default)
    for subprop in prop:
        try:
            return prop_dict[key][subprop]
        except KeyError:
            pass
    return default
def SetProp(prop_dict, key, prop, value):
    if not key in prop_dict:
        prop_dict[key] = {prop: value}
    else:
        prop_dict[key][prop] = value
def DelProp(prop_dict, key, prop):
    try:
        del prop_dict[key][prop]
    except KeyError:
        pass

def GetPageProp(page, prop, default=None):
    global PageProps
    return GetProp(PageProps, page, prop, default)
def SetPageProp(page, prop, value):
    global PageProps
    SetProp(PageProps, page, prop, value)
def DelPageProp(page, prop):
    global PageProps
    DelProp(PageProps, page, prop)
def GetTristatePageProp(page, prop, default=0):
    res = GetPageProp(page, prop, default)
    if res != FirstTimeOnly: return res
    return (GetPageProp(page, '_shown', 0) == 1)

def GetFileProp(page, prop, default=None):
    global FileProps
    return GetProp(FileProps, page, prop, default)
def SetFileProp(page, prop, value):
    global FileProps
    SetProp(FileProps, page, prop, value)

# the Impressive logo (256x64 pixels grayscale PNG)
LOGO = """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"""
# the default cursor (19x23 pixel RGBA PNG)
DEFAULT_CURSOR = """iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAADCklEQVR42qWUXWwMURTH787MznbWbm1VtdWP0KBN+pFWlQRVQlJBQkR4lGqioY0IibSprAchHgQhoh76hAQPJB4IRdBobdFstbZ4oJLup9au3c5Md3fmjnPHdE2qZVsn+c3snDv3v/9zzt2lEcRbx90rnAk/d7x2xdF/BAWwFmv6jm1bal4db95Xp
uVmLcbEJfQ9Y0Fu8YZ1yzsvnTu6G3LG2YopPM+HbfMWohTObC0pWXLjWrv9DOS52YjJAi8EKJpBqbZMxNAMlZeXdeTOzdP36/duzYF1w4yciSI/gmUJxLIQw7CIomiUZrOu37m9puukvW51sn0kL2FBEN0Yy2qClGswUIiijYjjUvJXrijuaLt4uCGZPv7qmTAWIGIKMMeajliTGQQNqkOGYbiCxTmXr7e3XC0tXmT5mxhNLtVrq3KWLS3YQxw
RjCyHBD6IFPUVclUMHGeqWFVVWJuXm/Gku2cwNK0zr9fvJc5UdwqGqVoRZ56rOjMAFMWon1NTLZU11WXdZ0/Vb56qj2ri0eOXwzAAnBDEGKWl56oCk2FZNqOoMP9e24XG5sl9VMv0+0eM9XW7mhijkSXPpF+M0YRkOY7iMVFfbsKE1cJtrN1UXmrmUjr6XUMi0lmVYKKj5Hjo3dnSshENU9WXS75IxgoOhfmxWEwurSwvaIX96mCYCbFoNBrEW
MqnMK0JSurx6HcNhxwOR8TnHx33eALjXt+o4A8EBUVReNjnBgaALGBoQkwWRRGOB1ZFDJhSBV90OoIHmuxOWZZ98E4Q4HVEgDDgAUiZyoQYjsbiI2SSMpRKynrv+jR2sKmlF4TewLpD20RExrXNMY24dpcTYvBj94F1RHC7vdH9Dcf6eF5wwtpDwKk5wZMnoY/fzqIxH3EWiQhS46ETAz7/t3eQfwqQe2g6gT/OGYkfobBHisfkVvv5vg8fP/d
D6hnQq/Xqn0KJc0aiorxofq9zkL11+8FXeOwCOgGfVlpSof+vygTWAGagB/iiNTfp0IsRkWxA0hxFZyI0lbBRX/pM4ycZx2V6yAv08AAAAABJRU5ErkJggg=="""

# get the contents of a PIL image as a string
def img2str(img):
    if hasattr(img, "tobytes"):
        return img.tobytes()
    else:
        return img.tostring()

# create a PIL image from a string
def str2img(mode, size, data):
    if hasattr(Image, "frombytes"):
        return Image.frombytes(mode, size, data)
    else:
        return Image.fromstring(mode, size, data)

# determine the next power of two
def npot(x):
    res = 1
    while res < x: res <<= 1
    return res

# convert boolean value to string
def b2s(b):
    if b: return "Y"
    return "N"

# extract a number at the beginning of a string
def num(s):
    s = s.strip()
    r = ""
    while s[0] in "0123456789":
        r += s[0]
        s = s[1:]
    try:
        return int(r)
    except ValueError:
        return -1

# linearly interpolate between two floating-point RGB colors represented as tuples
def lerpColor(a, b, t):
    return tuple([min(1.0, max(0.0, x + t * (y - x))) for x, y in zip(a, b)])

# get a representative subset of file statistics
def my_stat(filename):
    try:
        s = os.stat(filename)
    except OSError:
        return None
    return (s.st_size, s.st_mtime, s.st_ctime, s.st_mode)

# determine (pagecount,width,height) of a PDF file
def analyze_pdf(filename):
    f = file(filename,"rb")
    pdf = f.read()
    f.close()
    box = map(float, pdf.split("/MediaBox",1)[1].split("]",1)[0].split("[",1)[1].strip().split())
    return (max(map(num, pdf.split("/Count")[1:])), box[2]-box[0], box[3]-box[1])

# unescape &#123; literals in PDF files
re_unescape = re.compile(r'&#[0-9]+;')
def decode_literal(m):
    try:
        code = int(m.group(0)[2:-1])
        if code:
            return chr(code)
        else:
            return ""
    except ValueError:
        return '?'
def unescape_pdf(s):
    return re_unescape.sub(decode_literal, s)

# parse pdftk output
def pdftkParse(filename, page_offset=0):
    f = file(filename, "r")
    InfoKey = None
    BookmarkTitle = None
    Title = None
    Pages = 0
    for line in f:
        try:
            key, value = [item.strip() for item in line.split(':', 1)]
        except ValueError:
            continue
        key = key.lower()
        if key == "numberofpages":
            Pages = int(value)
        elif key == "infokey":
            InfoKey = value.lower()
        elif (key == "infovalue") and (InfoKey == "title"):
            Title = unescape_pdf(value)
            InfoKey = None
        elif key == "bookmarktitle":
            BookmarkTitle = unescape_pdf(value)
        elif key == "bookmarkpagenumber" and BookmarkTitle:
            try:
                page = int(value)
                if not GetPageProp(page + page_offset, '_title'):
                    SetPageProp(page + page_offset, '_title', BookmarkTitle)
            except ValueError:
                pass
            BookmarkTitle = None
    f.close()
    if AutoOverview:
        SetPageProp(page_offset + 1, '_overview', True)
        for page in xrange(page_offset + 2, page_offset + Pages):
            SetPageProp(page, '_overview', \
                        not(not(GetPageProp(page + AutoOverview - 1, '_title'))))
        SetPageProp(page_offset + Pages, '_overview', True)
    return (Title, Pages)

# parse mutool output
def mutoolParse(f, page_offset=0):
    title = None
    pages = 0
    for line in f:
        m = re.match("pages:\s*(\d+)", line, re.I)
        if m and not(pages):
            pages = int(m.group(1))
        m = re.search("/title\s*\(", line, re.I)
        if m and not(title):
            title = line[m.end():].replace(')', '\0').replace('\\(', '(').replace('\\\0', ')').split('\0', 1)[0].strip()
    return (title, pages)

# translate pixel coordinates to normalized screen coordinates
def MouseToScreen(mousepos):
    return (ZoomX0 + mousepos[0] * ZoomArea / ScreenWidth,
            ZoomY0 + mousepos[1] * ZoomArea / ScreenHeight)

# normalize rectangle coordinates so that the upper-left point comes first
def NormalizeRect(X0, Y0, X1, Y1):
    return (min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1))

# check if a point is inside a box (or a list of boxes)
def InsideBox(x, y, box):
    return (x >= box[0]) and (y >= box[1]) and (x < box[2]) and (y < box[3])
def FindBox(x, y, boxes):
    for i in xrange(len(boxes)):
        if InsideBox(x, y, boxes[i]):
            return i
    raise ValueError

# zoom an image size to a destination size, preserving the aspect ratio
def ZoomToFit(size, dest=None):
    if not dest:
        dest = (ScreenWidth + Overscan, ScreenHeight + Overscan)
    newx = dest[0]
    newy = size[1] * newx / size[0]
    if newy > dest[1]:
        newy = dest[1]
        newx = size[0] * newy / size[1]
    return (newx, newy)

# get the overlay grid screen coordinates for a specific page
def OverviewPos(page):
    return ( \
        int(page % OverviewGridSize) * OverviewCellX + OverviewOfsX, \
        int(page / OverviewGridSize) * OverviewCellY + OverviewOfsY  \
    )

def StopMPlayer():
    global MPlayerProcess, VideoPlaying, NextPageAfterVideo
    if not MPlayerProcess: return

    # first, ask politely
    try:
        if Platform.use_omxplayer and VideoPlaying:
            MPlayerProcess.stdin.write('q')
        else:
            MPlayerProcess.stdin.write('quit\n')
        MPlayerProcess.stdin.flush()
        for i in xrange(10):
            if MPlayerProcess.poll() is None:
                time.sleep(0.1)
            else:
                break
    except:
        pass

    # if that didn't work, be rude
    if MPlayerProcess.poll() is None:
        print >>sys.stderr, "Audio/video player didn't exit properly, killing PID", MPlayerProcess.pid
        try:
            if os.name == 'nt':
                win32api.TerminateProcess(win32api.OpenProcess(1, False, MPlayerProcess.pid), 0)
            else:
                os.kill(MPlayerProcess.pid, 2)
            MPlayerProcess = None
        except:
            pass
    else:
        MPlayerProcess = None

    VideoPlaying = False
    if os.name == 'nt':
        win32gui.ShowWindow(Platform.GetWindowID(), 9)  # SW_RESTORE
    if NextPageAfterVideo:
        NextPageAfterVideo = False
        TransitionTo(GetNextPage(Pcurrent, 1))

def ClockTime(minutes):
    if minutes:
        return time.strftime("%H:%M")
    else:
        return time.strftime("%H:%M:%S")

def FormatTime(t, minutes=False):
    if minutes and (t < 3600):
        return "%d min" % (t / 60)
    elif minutes:
        return "%d:%02d" % (t / 3600, (t / 60) % 60)
    elif t < 3600:
        return "%d:%02d" % (t / 60, t % 60)
    else:
        ms = t % 3600
        return "%d:%02d:%02d" % (t / 3600, ms / 60, ms % 60)

def SafeCall(func, args=[], kwargs={}):
    if not func: return None
    try:
        return func(*args, **kwargs)
    except:
        print >>sys.stderr, "----- Unhandled Exception ----"
        traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "----- End of traceback -----"

def Quit(code=0):
    global CleanExit
    if not code:
        CleanExit = True
    StopMPlayer()
    Platform.Done()
    print >>sys.stderr, "Total presentation time: %s." % \
                        FormatTime((Platform.GetTicks() - StartTime) / 1000)
    sys.exit(code)
