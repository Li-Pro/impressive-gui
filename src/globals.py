##### GLOBAL VARIABLES #########################################################

# initialize private variables
FileName = ""
FileList = []
InfoScriptPath = None
Marking = False
Tracing = False
Panning = False
FileProps = {}
PageProps = {}
PageCache = {}
CacheFile = None
CacheFileName = None
CacheFilePos = 0
CacheMagic = ""
MPlayerProcess = None
VideoPlaying = False
MouseDownX = 0
MouseDownY = 0
MarkUL = (0, 0)
MarkLR = (0, 0)
ZoomX0 = 0.0
ZoomY0 = 0.0
ZoomArea = 1.0
ZoomMode = False
IsZoomed = False
ZoomWarningIssued = False
TransitionRunning = False
TransitionPhase = 0.0
CurrentCaption = 0
OverviewNeedUpdate = False
FileStats = None
OSDFont = None
CurrentOSDCaption = ""
CurrentOSDPage = ""
CurrentOSDStatus = ""
CurrentOSDComment = ""
Lrender = create_lock()
Lcache = create_lock()
Loverview = create_lock()
RTrunning = False
RTrestart = False
StartTime = 0
CurrentTime = 0
PageEnterTime = 0
PageLeaveTime = 0
PageTimeout = 0
TimeDisplay = False
TimeTracking = False
FirstPage = True
ProgressBarPos = 0
CursorVisible = True
OverviewMode = False
LastPage = 0
WantStatus = False

# tool constants (used in info scripts)
FirstTimeOnly = 2

# event constants
USEREVENT_HIDE_MOUSE = USEREVENT
USEREVENT_PAGE_TIMEOUT = USEREVENT + 1
USEREVENT_POLL_FILE = USEREVENT + 2
USEREVENT_TIMER_UPDATE = USEREVENT + 3
