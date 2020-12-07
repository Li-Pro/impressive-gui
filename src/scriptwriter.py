##### INFO SCRIPT I/O ##########################################################

# info script reader
def LoadInfoScript():
    global PageProps
    try:
        os.chdir(os.path.dirname(InfoScriptPath) or BaseWorkingDir)
    except OSError:
        pass
    OldPageProps = PageProps
    try:
        execfile(InfoScriptPath, globals())
    except IOError:
        pass
    except:
        print("----- Exception in info script ----", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("----- End of traceback -----", file=sys.stderr)
    NewPageProps = PageProps
    PageProps = OldPageProps
    del OldPageProps
    for page in NewPageProps:
        for prop in NewPageProps[page]:
            SetPageProp(page, prop, NewPageProps[page][prop])
    del NewPageProps

# we can't save lambda expressions, so we need to warn the user
# in every possible way
ScriptTainted = False
LambdaWarning = False
def here_was_a_lambda_expression_that_could_not_be_saved():
    global LambdaWarning
    if not LambdaWarning:
        print("WARNING: The info script for the current file contained lambda expressions that", file=sys.stderr)
        print("         were removed during the a save operation.", file=sys.stderr)
        LambdaWarning = True

# "clean" a PageProps entry so that only 'public' properties are left
def GetPublicProps(props):
    props = props.copy()
    # delete private (underscore) props
    for prop in list(props.keys()):
        if str(prop)[0] == '_':
            del props[prop]
    # clean props to default values
    if props.get('overview', False):
        del props['overview']
    if not props.get('skip', True):
        del props['skip']
    if ('boxes' in props) and not(props['boxes']):
        del props['boxes']
    return props

# helper definitions for PropValueRepr
class dummyClass(object): pass
typesFunctionType = type(GetPublicProps)

# Generate a string representation of a property value.
# Mainly this converts classes or instances to the name of the class.
def PropValueRepr(value):
    global ScriptTainted
    if type(value) == typesFunctionType:
        if value.__name__ != "<lambda>":
            return value.__name__
        if not ScriptTainted:
            print("WARNING: The info script contains lambda expressions, which cannot be saved", file=sys.stderr)
            print("         back. The modifed script will be written into a separate file to", file=sys.stderr)
            print("         minimize data loss.", file=sys.stderr)
            ScriptTainted = True
        return "here_was_a_lambda_expression_that_could_not_be_saved"
    elif isinstance(value, type):  # transition class
        return value.__name__
    elif isinstance(value, Transition):  # transition instance
        return value.__class__.__name__
    elif isinstance(value, dict):
        return "{ " + ", ".join([PropValueRepr(k) + ": " + PropValueRepr(value[k]) for k in value]) + " }"
    else:
        value = repr(value)
        if value.startswith(('u"', "u'")):  # strip unicode prefixes on Python 2
            value = value[1:]
        return value

# generate a nicely formatted string representation of a page's properties
def SinglePagePropRepr(page):
    props = GetPublicProps(PageProps[page])
    if not props: return None
    return "\n%3d: {%s\n     }" % (page, \
        ",".join(["\n       " + repr(prop) + ": " + PropValueRepr(props[prop]) for prop in props]))

# generate a nicely formatted string representation of all page properties
def PagePropRepr():
    pages = list(PageProps.keys())
    pages.sort()
    return "PageProps = {%s\n}" % (",".join(filter(None, map(SinglePagePropRepr, pages))))

# count the characters of a python dictionary source code, correctly handling
# embedded strings and comments, and nested dictionaries
def CountDictChars(s, start=0):
    context = None
    level = 0
    for i in range(start, len(s)):
        c = s[i]
        if context is None:
            if c == '{': level += 1
            if c == '}': level -= 1
            if c == '#': context = '#'
            if c == '"': context = '"'
            if c == "'": context = "'"
        elif context[0] == "\\":
            context=context[1]
        elif context == '#':
            if c in "\r\n": context = None
        elif context == '"':
            if c == "\\": context = "\\\""
            if c == '"': context = None
        elif context == "'":
            if c == "\\": context = "\\'"
            if c == "'": context = None
        if level < 0: return i
    raise ValueError("the dictionary never ends")

# modify and save a file's info script
def SaveInfoScript(filename):
    # read the old info script
    try:
        f = open(filename, "r")
        script = f.read()
        f.close()
    except IOError:
        script = ""
    if not script:
        script = "# -*- coding: utf-8 -*-\n"

    # replace the PageProps of the old info script with the current ones
    try:
        m = re.search("^.*(PageProps)\s*=\s*(\{).*$", script,re.MULTILINE)
        if m:
            script = script[:m.start(1)] + PagePropRepr() + \
                     script[CountDictChars(script, m.end(2)) + 1 :]
        else:
            script += "\n" + PagePropRepr() + "\n"
    except (AttributeError, ValueError):
        pass

    if ScriptTainted:
        filename += ".modified"

    # write the script back
    try:
        f = open(filename, "w")
        f.write(script)
        f.close()
    except:
        print("Oops! Could not write info script!", file=sys.stderr)
