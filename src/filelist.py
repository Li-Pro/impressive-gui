##### FILE LIST GENERATION #####################################################

def IsImageFileName(name):
    return os.path.splitext(name)[1].lower() in \
           (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".ppm", ".pgm")
def IsPlayable(name):
    return IsImageFileName(name) or name.lower().endswith(".pdf") or os.path.isdir(name)

def AddFile(name, title=None, implicit=False):
    global FileList, FileName

    # handle list files
    if name.startswith('@') and os.path.isfile(name[1:]):
        name = name[1:]
        dirname = os.path.dirname(name)
        try:
            f = file(name, "r")
            next_title = None
            for line in f:
                line = [part.strip() for part in line.split('#', 1)]
                if len(line) == 1:
                    subfile = line[0]
                    title = None
                else:
                    subfile, title = line
                if subfile:
                    AddFile(os.path.normpath(os.path.join(dirname, subfile)), title, implicit=True)
            f.close()
        except IOError:
            print >>sys.stderr, "Error: cannot read list file `%s'" % name
        return

    # generate absolute path
    path_sep_at_end = name.endswith(os.path.sep)
    name = os.path.normpath(os.path.abspath(name)).rstrip(os.path.sep)
    if path_sep_at_end:
        name += os.path.sep

    # set FileName to first (explicitly specified) input file
    if not implicit:
        if not FileList:
            FileName = name
        else:
            FileName = ""

    if os.path.isfile(name):
        FileList.append(name)
        if title: SetFileProp(name, 'title', title)

    elif os.path.isdir(name):
        images = [os.path.join(name, f) for f in os.listdir(name) if IsImageFileName(f)]
        images.sort(lambda a, b: cmp(a.lower(), b.lower()))
        if not images:
            print >>sys.stderr, "Warning: no image files in directory `%s'" % name
        for img in images:
            AddFile(img, implicit=True)

    else:
        files = list(filter(IsPlayable, glob.glob(name)))
        if files:
            for f in files: AddFile(f, implicit=True)
        else:
            print >>sys.stderr, "Error: input file `%s' not found" % name
