##### PAGE CACHE MANAGEMENT ####################################################

# helper class that allows PIL to write and read image files with an offset
class IOWrapper:
    def __init__(self, f, offset=0):
        self.f = f
        self.offset = offset
        self.f.seek(offset)
    def read(self, count=None):
        if count is None:
            return self.f.read()
        else:
            return self.f.read(count)
    def write(self, data):
        self.f.write(data)
    def seek(self, pos, whence=0):
        assert(whence in (0, 1))
        if whence:
            self.f.seek(pos, 1)
        else:
            self.f.seek(pos + self.offset)
    def tell(self):
        return self.f.tell() - self.offset

# generate a "magic number" that is used to identify persistent cache files
def UpdateCacheMagic():
    global CacheMagic
    pool = [PageCount, ScreenWidth, ScreenHeight, b2s(Scaling), b2s(Supersample), b2s(Rotation)]
    flist = list(FileProps.keys())
    flist.sort(lambda a,b: cmp(a.lower(), b.lower()))
    for f in flist:
        pool.append(f)
        pool.extend(list(GetFileProp(f, 'stat', [])))
    CacheMagic = md5obj("\0".join(map(str, pool))).hexdigest()

# set the persistent cache file position to the current end of the file
def UpdatePCachePos():
    global CacheFilePos
    CacheFile.seek(0, 2)
    CacheFilePos = CacheFile.tell()

# rewrite the header of the persistent cache
def WritePCacheHeader(reset=False):
    pages = ["%08x" % PageCache.get(page, 0) for page in range(1, PageCount+1)]
    CacheFile.seek(0)
    CacheFile.write(CacheMagic + "".join(pages))
    if reset:
        CacheFile.truncate()
    UpdatePCachePos()

# return an image from the persistent cache or None if none is available
def GetPCacheImage(page):
    if CacheMode != PersistentCache:
        return  # not applicable if persistent cache isn't used
    Lcache.acquire()
    try:
        if page in PageCache:
            img = Image.open(IOWrapper(CacheFile, PageCache[page]))
            img.load()
            return img
    finally:
        Lcache.release()

# returns an image from the non-persistent cache or None if none is available
def GetCacheImage(page):
    if CacheMode in (NoCache, PersistentCache):
        return  # not applicable in uncached or persistent-cache mode
    Lcache.acquire()
    try:
        if page in PageCache:
            if CacheMode == FileCache:
                CacheFile.seek(PageCache[page])
                return CacheFile.read(TexSize)
            elif CacheMode == CompressedCache:
                return zlib.decompress(PageCache[page])
            else:
                return PageCache[page]
    finally:
        Lcache.release()

# adds an image to the persistent cache
def AddToPCache(page, img):
    if CacheMode != PersistentCache:
        return  # not applicable if persistent cache isn't used
    Lcache.acquire()
    try:
        if page in PageCache:
            return  # page is already cached and we can't update it safely
                    # -> stop here (the new image will be identical to the old
                    #    one anyway)
        img.save(IOWrapper(CacheFile, CacheFilePos), "ppm")
        PageCache[page] = CacheFilePos
        WritePCacheHeader()
    finally:
        Lcache.release()

# adds an image to the non-persistent cache
def AddToCache(page, data):
    global CacheFilePos
    if CacheMode in (NoCache, PersistentCache):
        return  # not applicable in uncached or persistent-cache mode
    Lcache.acquire()
    try:
        if CacheMode == FileCache:
            if not(page in PageCache):
                PageCache[page] = CacheFilePos
                CacheFilePos += len(data)
            CacheFile.seek(PageCache[page])
            CacheFile.write(data)
        elif CacheMode == CompressedCache:
            PageCache[page] = zlib.compress(data, 1)
        else:
            PageCache[page] = data
    finally:
        Lcache.release()

# invalidates the whole cache
def InvalidateCache():
    global PageCache, CacheFilePos
    Lcache.acquire()
    try:
        PageCache = {}
        if CacheMode == PersistentCache:
            UpdateCacheMagic()
            WritePCacheHeader(True)
        else:
            CacheFilePos = 0
    finally:
        Lcache.release()

# initialize the persistent cache
def InitPCache():
    global CacheFile, CacheMode

    # try to open the pre-existing cache file
    try:
        CacheFile = file(CacheFileName, "rb+")
    except IOError:
        CacheFile = None

    # check the cache magic
    UpdateCacheMagic()
    if CacheFile and (CacheFile.read(32) != CacheMagic):
        print >>sys.stderr, "Cache file mismatch, recreating cache."
        CacheFile.close()
        CacheFile = None

    if CacheFile:
        # if the magic was valid, import cache data
        print >>sys.stderr, "Using already existing persistent cache file."
        for page in range(1, PageCount+1):
            offset = int(CacheFile.read(8), 16)
            if offset:
                PageCache[page] = offset
        UpdatePCachePos()
    else:
        # if the magic was invalid or the file didn't exist, (re-)create it
        try:
            CacheFile = file(CacheFileName, "wb+")
        except IOError:
            print >>sys.stderr, "Error: cannot write the persistent cache file (`%s')" % CacheFileName
            print >>sys.stderr, "Falling back to temporary file cache."
            CacheMode = FileCache
        WritePCacheHeader()
