##### FILE LIST GENERATION #####################################################

def IsImageFileName(name):
    return os.path.splitext(name)[1].lower() in \
           (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".ppm", ".pgm")
def IsPlayable(name):
    return IsImageFileName(name) or name.lower().endswith(".pdf") or os.path.isdir(name)

def AddFile(name, title=None):
    global FileList, FileName

    if os.path.isfile(name):
        FileList.append(name)
        if title: SetFileProp(name, 'title', title)

    elif os.path.isdir(name):
        images = [os.path.join(name, f) for f in os.listdir(name) if IsImageFileName(f)]
        images.sort(lambda a, b: cmp(a.lower(), b.lower()))
        if not images:
            print >>sys.stderr, "Warning: no image files in directory `%s'" % name
        for img in images: AddFile(img)

    elif name.startswith('@') and os.path.isfile(name[1:]):
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
                    AddFile(os.path.normpath(os.path.join(dirname, subfile)), title)
            f.close()
        except IOError:
            print >>sys.stderr, "Error: cannot read list file `%s'" % name
        if not FileName:
            FileName = name
        else:
            FileName = ""

    else:
        files = list(filter(IsPlayable, glob.glob(name)))
        if files:
            for f in files: AddFile(f)
        else:
            print >>sys.stderr, "Error: input file `%s' not found" % name
