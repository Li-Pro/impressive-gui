##### EVENT-TO-ACTION BINDING CODE #############################################

SpecialKeyNames = set("""
ampersand asterisk at backquote backslash backspace break capslock caret clear
comma down escape euro end exclaim greater hash help home insert kp_divide
kp_enter kp_equals kp_minus kp_multiply kp_plus lalt last lctrl left leftbracket
leftparen less lmeta lshift lsuper menu minus mode numlock pagedown pageup pause
period plus power print question quote quotedbl ralt rctrl return right
rightbracket rightparen rmeta rshift rsuper scrollock semicolon slash space
sysreq tab underscore up
""".split())
KnownEvents = set(list(SpecialKeyNames) + """
a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9
kp0 kp1 kp2 kp3 kp4 kp5 kp6 kp7 kp8 kp9 f1 f2 f3 f4 f5 f6 f7 f8 f9 f10 f11 f12
lmb mmb rmb wheeldown wheelup
""".split() + ["btn%d" % i for i in range(1, 20)])

# event handling model:
# - Platform.GetEvent() generates platform-neutral event (= string) that
#   identifies a key or mouse button, with prefix:
#   - '+' = key pressed, '-' = key released, '*' = main event ('*' is generated
#      directly before '-' for keys and directly after '+' for mouse buttons)
#   - "ctrl+", "alt+", "shift+" modifiers, in that order
# - event gets translated into a list of actions via the EventMap dictionary
# - actions are processed in order of that list, like priorities:
#   - list processing terminates at the first action that is successfully handled
#   - exception: "forced actions" will always be executed, even if a higher-prio
#     action of that list has already been executed; also, they will not stop
#     action list execution, even if they have been handled

KnownActions = {}
EventMap = {}
ForcedActions = set()
ActivateReleaseActions = set()

class ActionNotHandled(Exception):
    pass

def ActionValidIf(cond):
    if not cond:
        raise ActionNotHandled()

class ActionRelayBase(object):
    def __init__(self):
        global KnownActions, ActivateReleaseActions
        for item in dir(self):
            if (item[0] == '_') and (item[1] != '_') and (item[1] != 'X') and (item[-1] != '_'):
                doc = getattr(self, item).__doc__
                if item.endswith("_ACTIVATE"):
                    item = item[:-9]
                    ActivateReleaseActions.add(item)
                elif item.endswith("_RELEASE"):
                    item = item[:-8]
                    ActivateReleaseActions.add(item)
                item = item[1:].replace('_', '-')
                olddoc = KnownActions.get(item)
                if not olddoc:
                    KnownActions[item] = doc

    def __call__(self, ev):
        evname = ev[1:].replace('-', '_')
        if ev[0] == '$':
            meth = getattr(self, '_X_' + evname, None)
        elif ev[0] == '*':
            meth = getattr(self, '_' + evname, None)
        elif ev[0] == '+':
            meth = getattr(self, '_' + evname + '_ACTIVATE', None)
        elif ev[0] == '-':
            meth = getattr(self, '_' + evname + '_RELEASE', None)
        if not meth:
            return False
        try:
            meth()
            return True
        except ActionNotHandled:
            return False

def ProcessEvent(ev, handler_func):
    """
    calls the appropriate action handlers for an event
    as returned by Platform.GetEvent()
    """
    if not ev:
        return False
    if ev[0] == '$':
        handler_func(ev)
    try:
        events = EventMap[ev[1:]]
    except KeyError:
        return False
    prefix = ev[0]
    handled = False
    no_forced = not(any(((prefix + ev) in ForcedActions) for ev in events))
    if no_forced and (prefix in "+-"):
        if not(any((ev in ActivateReleaseActions) for ev in events)):
            return False
    for ev in events:
        ev = prefix + ev
        if ev in ForcedActions:
            handler_func(ev)
        elif not handled:
            handled = handler_func(ev)
        if handled and no_forced:
            break
    return handled

def ValidateEvent(ev, error_prefix=None):
    for prefix in ("ctrl+", "alt+", "shift+"):
        if ev.startswith(prefix):
            ev = ev[len(prefix):]
    if (ev in KnownEvents) or ev.startswith('unknown-'):
        return True
    if error_prefix:
        error_prefix += ": "
    else:
        error_prefix = ""
    print("ERROR: %signoring unknown event '%s'" % (error_prefix, ev), file=sys.stderr)
    return False

def ValidateAction(ev, error_prefix=None):
    if not(KnownActions) or (ev in KnownActions):
        return True
    if error_prefix:
        error_prefix += ": "
    else:
        error_prefix = ""
    print("ERROR: %signoring unknown action '%s'" % (error_prefix, ev), file=sys.stderr)
    return False

def BindEvent(events, actions=None, clear=False, remove=False, error_prefix=None):
    """
    bind one or more events to one or more actions
    - events and actions can be lists or single comma-separated strings
    - if clear is False, actions will be *added* to the raw events,
      if clear is True, the specified actions will *replace* the current set,
      if remove is True, the specified actions will be *removed* from the set
    - actions can be omitted; instead, events can be a string consisting
      of raw event and internal event names, separated by one of:
        '=' -> add or replace, based on the clear flag
        '+=' -> always add
        ':=' -> always clear
        '-=' -> always remove
    - some special events are recognized:
        'clearall' clears *all* actions of *all* raw events;
        'defaults' loads all defaults
        'include', followed by whitespace and a filename, will include a file
        (that's what the basedirs option is for)
    """
    global EventMap
    if isinstance(events, basestring):
        if not actions:
            if (';' in events) or ('\n' in events):
                for cmd in events.replace('\n', ';').split(';'):
                    BindEvent(cmd, clear=clear, remove=remove, error_prefix=error_prefix)
                return
            if '=' in events:
                events, actions = events.split('=', 1)
                events = events.rstrip()
                if events.endswith('+'):
                    clear = False
                    events = events[:-1]
                elif events.endswith(':'):
                    clear = True
                    events = events[:-1]
                elif events.endswith('-'):
                    remove = True
                    events = events[:-1]
        events = events.split(',')
    if actions is None:
        actions = []
    elif isinstance(actions, basestring):
        actions = actions.split(',')
    actions = [b.replace('_', '-').strip(' \t$+-').lower() for b in actions]
    actions = [a for a in actions if ValidateAction(a, error_prefix)]
    for event in events:
        event_orig = event.replace('\t', ' ').strip(' \r\n+-$')
        if not event_orig:
            continue
        event = event_orig.replace('-', '_').lower()
        if event.startswith('include '):
            filename = event_orig[8:].strip()
            if (filename.startswith('"') and filename.endswith('"')) \
            or (filename.startswith("'") and filename.endswith("'")):
                filename = filename[1:-1]
            ParseInputBindingFile(filename)
            continue
        elif event == 'clearall':
            EventMap = {}
            continue
        elif event == 'defaults':
            LoadDefaultBindings()
            continue
        event = event.replace(' ', '')
        if not ValidateEvent(event, error_prefix):
            continue
        if remove:
            if event in EventMap:
                for a in actions:
                    try:
                        EventMap[event].remove(a)
                    except ValueError:
                        pass
        elif clear or not(event in EventMap):
            EventMap[event] = actions[:]
        else:
            EventMap[event].extend(actions)

def ParseInputBindingFile(filename):
    """
    parse an input configuration file;
    basically calls BindEvent() for each line;
    '#' is the comment character
    """
    try:
        f = open(filename, "r")
        n = 0
        for line in f:
            n += 1
            line = line.split('#', 1)[0].strip()
            if line:
                BindEvent(line, error_prefix="%s:%d" % (filename, n))
        f.close()
    except IOError as e:
        print("ERROR: failed to read the input configuration file '%s' -" % filename, e, file=sys.stderr)

def EventHelp():
    evlist = ["a-z", "0-9", "kp0-kp9", "f1-f12"] + sorted(list(SpecialKeyNames))
    print("Event-to-action binding syntax:")
    print("  <event> [,<event2...>] = <action> [,<action2...>]")
    print("  By default, this will *add* actions to an event.")
    print("  To *overwrite* the current binding for an event, use ':=' instead of '='.")
    print("  To remove actions from an event, use '-=' instead of '='.")
    print("  Join multiple bindings with a semi-colon (';').")
    print("Special commands:")
    print("  clearall       = clear all bindings")
    print("  defaults       = load default bindings")
    print("  include <file> = load bindings from a file")
    print("Binding files use the same syntax with one binding per line;")
    print("comments start with a '#' symbol.")
    print()
    print("Recognized keyboard event names:")
    while evlist:
        line = "  "
        while evlist and ((len(line) + len(evlist[0])) < 78):
            line += evlist.pop(0) + ", "
        line = line.rstrip()
        if not evlist:
            line = line.rstrip(',')
        print(line)
    print("Recognized mouse event names:")
    print("  lmb, mmb, rmb (= left, middle and right mouse buttons),")
    print("  wheelup, wheeldown,")
    print("  btnX (additional buttons, use --evtest to check their mapping)")
    print()
    print("Recognized actions:")
    maxalen = max(map(len, KnownActions))
    for action in sorted(KnownActions):
        doc = KnownActions[action]
        if doc:
            print("  %s - %s" % (action.ljust(maxalen), doc))
        else:
            print("  %s" % action)
    print()
    if not EventMap: return
    print("Current bindings:")
    maxelen = max(map(len, EventMap))
    for event in sorted(EventMap):
        if EventMap[event]:
            print("  %s = %s" % (event.ljust(maxelen), ", ".join(EventMap[event])))

def LoadDefaultBindings():
    BindEvent("""clearall
    escape, return, kp_enter, lmb, rmb = video-stop
    space = video-pause
    period = video-step
    down = video-seek-backward-10
    left = video-seek-backward-1
    right = video-seek-forward-1
    up = video-seek-forward-10

    escape = overview-exit, zoom-exit, spotlight-exit, box-clear, quit
    q = quit
    f = fullscreen
    tab = overview-enter, overview-exit
    s = save
    a = auto-toggle
    t = time-toggle
    r = time-reset
    c = box-clear
    y, z = zoom-enter, zoom-exit
    o = toggle-overview
    i = toggle-skip
    u = zoom-update
    b, period = fade-to-black
    w, comma = fade-to-white
    return, kp_enter = overview-confirm, spotlight-enter, spotlight-exit
    plus, kp_plus, 0, wheelup = spotlight-grow
    minus, kp_minus, 9, wheeldown = spotlight-shrink
    ctrl+9, ctrl+0 = spotlight-reset
    7 = fade-less
    8 = fade-more
    ctrl+7, ctrl+8 = fade-reset
    leftbracket = gamma-decrease
    rightbracket = gamma-increase
    shift+leftbracket = gamma-bl-decrease
    shift+rightbracket = gamma-bl-increase
    backslash = gamma-reset
    lmb = box-add, hyperlink, overview-confirm
    ctrl+lmb = box-zoom, hyperlink-notrans
    rmb = box-zoom-exit, zoom-pan, box-remove, overview-exit
    mmb = zoom-pan, zoom-exit, overview-enter, overview-exit
    left, wheelup = overview-prev
    right, wheeldown = overview-next
    up = overview-up
    down = overview-down
    wheelup = zoom-in
    wheeldown = zoom-out

    lmb, wheeldown, pagedown, down, right, space = goto-next
    ctrl+lmb, ctrl+wheeldown, ctrl+pagedown, ctrl+down, ctrl+right, ctrl+space = goto-next-notrans
    rmb, wheelup, pageup, up, left, backspace = goto-prev
    ctrl+rmb, ctrl+wheelup, ctrl+pageup, ctrl+up, ctrl+left, ctrl+backspace = goto-prev-notrans
    home = goto-start
    ctrl+home = goto-start-notrans
    end = goto-end
    ctrl+end = goto-end-notrans
    l = goto-last
    ctrl+l = goto-last-notrans
    """, error_prefix="LoadDefaultBindings")

# basic action implementations (i.e. stuff that is required to work in all modes)
class BaseActions(ActionRelayBase):
    def _X_quit(self):
        Quit()

    def _X_alt_tab(self):
        ActionValidIf(Fullscreen)
        SetFullscreen(False)
        Platform.Minimize()

    def _quit(self):
        "quit Impressive immediately"
        Platform.PostQuitEvent()

    def _X_move(self):
        # mouse move in fullscreen mode -> show mouse cursor and reset mouse timer
        if Fullscreen:
            Platform.ScheduleEvent("$hide-mouse", MouseHideDelay)
            SetCursor(True)

    def _X_call(self):
        while CallQueue:
            func, args, kwargs = CallQueue.pop(0)
            func(*args, **kwargs)
