##### FILE LIST GENERATION #####################################################

ImageExts = set('.'+x for x in "jpg jpeg png tif tiff bmp ppm pgm".split())
VideoExts = set('.'+x for x in "avi mov mp4 mkv ogv mpg mpeg m1v m2v m4v mts m2ts m2t ts webm 3gp flv qt".split())
AllExts = set(list(ImageExts) + list(VideoExts) + [".pdf"])

def CheckExt(name, exts):
    return os.path.splitext(name)[1].lower() in exts
def IsImageFile(name): return CheckExt(name, ImageExts)
def IsVideoFile(name): return CheckExt(name, VideoExts)
def IsPlayable(name):  return CheckExt(name, AllExts)

def AddFile(name, title=None, implicit=False):
    global FileList, FileName

    # handle list files
    if name.startswith('@') and os.path.isfile(name[1:]):
        name = name[1:]
        dirname = os.path.dirname(name)
        try:
            f = open(name, "r")
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
            print("Error: cannot read list file `%s'" % name, file=sys.stderr)
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
        if IsPlayable(name):
            FileList.append(name)
            if title: SetFileProp(name, 'title', title)
        else:
            print("Warning: input file `%s' has unrecognized file type" % name, file=sys.stderr)

    elif os.path.isdir(name):
        images = [os.path.join(name, f) for f in os.listdir(name) if IsImageFile(f)]
        images.sort(key=lambda f: f.lower())
        if not images:
            print("Warning: no image files in directory `%s'" % name, file=sys.stderr)
        for img in images:
            AddFile(img, implicit=True)

    else:
        files = list(filter(IsPlayable, glob.glob(name)))
        if files:
            for f in files: AddFile(f, implicit=True)
        else:
            print("Error: input file `%s' not found" % name, file=sys.stderr)
