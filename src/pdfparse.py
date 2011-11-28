##### PDF PARSER ###############################################################

class PDFError(Exception):
    pass

class PDFref:
    def __init__(self, ref):
        self.ref = ref
    def __repr__(self):
        return "PDFref(%d)" % self.ref

re_pdfstring = re.compile(r'\(\)|\(.*?[^\\]\)')
pdfstringrepl = [("\\"+x[0], x[1:]) for x in "(( )) n\n r\r t\t".split(" ")]
def pdf_maskstring(s):
    s = s[1:-1]
    for a, b in pdfstringrepl:
        s = s.replace(a, b)
    return " <" + "".join(["%02X"%ord(c) for c in s]) + "> "
def pdf_mask_all_strings(s):
    return re_pdfstring.sub(lambda x: pdf_maskstring(x.group(0)), s)
def pdf_unmaskstring(s):
    return "".join([chr(int(s[i:i+2], 16)) for i in xrange(1, len(s)-1, 2)])

class PDFParser:
    def __init__(self, filename):
        self.f = file(filename, "rb")
        self.errors = 0

        # find the first cross-reference table
        self.f.seek(0, 2)
        filesize = self.f.tell()
        self.f.seek(filesize - 128)
        trailer = self.f.read()
        i = trailer.rfind("startxref")
        if i < 0:
            raise PDFError, "cross-reference table offset missing"
        try:
            offset = int(trailer[i:].split("\n")[1].strip())
        except (IndexError, ValueError):
            raise PDFError, "malformed cross-reference table offset"

        # follow the trailer chain
        self.xref = {}
        while offset:
            newxref = self.xref
            self.xref, rootref, offset = self.parse_trailer(offset)
            self.xref.update(newxref)

        # scan the page and names tree
        self.obj2page = {}
        self.page2obj = {}
        self.annots = {}
        self.page_count = 0
        self.box = {}
        self.names = {}
        self.rotate = {}
        root = self.getobj(rootref, 'Catalog')
        try:
            self.scan_page_tree(root['Pages'].ref)
        except KeyError:
            raise PDFError, "root page tree node missing"
        try:
            self.scan_names_tree(root['Names'].ref)
        except KeyError:
            pass

    def getline(self):
        while True:
            line = self.f.readline().strip()
            if line: return line

    def find_length(self, tokens, begin, end):
        level = 1
        for i in xrange(1, len(tokens)):
            if tokens[i] == begin:  level += 1
            if tokens[i] == end:    level -= 1
            if not level: break
        return i + 1

    def parse_tokens(self, tokens, want_list=False):
        res = []
        while tokens:
            t = tokens[0]
            v = t
            tlen = 1
            if (len(tokens) >= 3) and (tokens[2] == 'R'):
                v = PDFref(int(t))
                tlen = 3
            elif t == "<<":
                tlen = self.find_length(tokens, "<<", ">>")
                v = self.parse_tokens(tokens[1 : tlen - 1], True)
                v = dict(zip(v[::2], v[1::2]))
            elif t == "[":
                tlen = self.find_length(tokens, "[", "]")
                v = self.parse_tokens(tokens[1 : tlen - 1], True)
            elif not(t) or (t[0] == "null"):
                v = None
            elif (t[0] == '<') and (t[-1] == '>'):
                v = pdf_unmaskstring(t)
            elif t[0] == '/':
                v = t[1:]
            elif t == 'null':
                v = None
            else:
                try:
                    v = float(t)
                    v = int(t)
                except ValueError:
                    pass
            res.append(v)
            del tokens[:tlen]
        if want_list:
            return res
        if not res:
            return None
        if len(res) == 1:
            return res[0]
        return res

    def parse(self, data):
        data = pdf_mask_all_strings(data)
        data = data.replace("<<", " << ").replace("[", " [ ").replace("(", " (")
        data = data.replace(">>", " >> ").replace("]", " ] ").replace(")", ") ")
        data = data.replace("/", " /").replace("><", "> <")
        return self.parse_tokens(filter(None, data.split()))

    def getobj(self, obj, force_type=None):
        if isinstance(obj, PDFref):
            obj = obj.ref
        if type(obj) != types.IntType:
            raise PDFError, "object is not a valid reference"
        offset = self.xref.get(obj, 0)
        if not offset:
            raise PDFError, "referenced non-existing PDF object"
        self.f.seek(offset)
        header = self.getline().split(None, 3)
        if (len(header) < 3) or (header[2] != "obj") or (header[0] != str(obj)):
            raise PDFError, "object does not start where it's supposed to"
        if len(header) == 4:
            data = [header[3]]
        else:
            data = []
        while True:
            line = self.getline()
            if line in ("endobj", "stream"): break
            data.append(line)
        data = self.parse(" ".join(data))
        if force_type:
            try:
                t = data['Type']
            except (KeyError, IndexError, ValueError):
                t = None
            if t != force_type:
                raise PDFError, "object does not match the intended type"
        return data

    def parse_xref_section(self, start, count):
        xref = {}
        for obj in xrange(start, start + count):
            line = self.getline()
            if line[-1] == 'f':
                xref[obj] = 0
            else:
                xref[obj] = int(line[:10], 10)
        return xref

    def parse_trailer(self, offset):
        self.f.seek(offset)
        xref = {}
        rootref = 0
        offset = 0
        if self.getline() != "xref":
            raise PDFError, "cross-reference table does not start where it's supposed to"
            return (xref, rootref, offset)   # no xref table found, abort
        # parse xref sections
        while True:
            line = self.getline()
            if line == "trailer": break
            start, count = map(int, line.split())
            xref.update(self.parse_xref_section(start, count))
        # parse trailer
        trailer = ""
        while True:
            line = self.getline()
            if line in ("startxref", "%%EOF"): break
            trailer += line
        trailer = self.parse(trailer)
        try:
            rootref = trailer['Root'].ref
        except KeyError:
            raise PDFError, "root catalog entry missing"
        except AttributeError:
            raise PDFError, "root catalog entry is not a reference"
        return (xref, rootref, trailer.get('Prev', 0))

    def scan_page_tree(self, obj, mbox=None, cbox=None, rotate=0):
        try:
            node = self.getobj(obj)
            if node['Type'] == 'Pages':
                for kid in node['Kids']:
                    self.scan_page_tree(kid.ref, \
                                        node.get('MediaBox', mbox), \
                                        node.get('CropBox', cbox), \
                                        node.get('Rotate', 0))
            else:
                page = self.page_count + 1
                anode = node.get('Annots', [])
                if anode.__class__ == PDFref:
                    anode = self.getobj(anode.ref)
                self.page_count = page
                self.obj2page[obj] = page
                self.page2obj[page] = obj
                self.box[page] = node.get('CropBox', cbox) or node.get('MediaBox', mbox)
                self.rotate[page] = node.get('Rotate', rotate)
                self.annots[page] = [a.ref for a in anode]
        except (KeyError, TypeError, ValueError):
            self.errors += 1

    def scan_names_tree(self, obj, come_from=None, name=None):
        try:
            node = self.getobj(obj)
            # if we came from the root node, proceed to Dests
            if not come_from:
                for entry in ('Dests', ):
                    if entry in node:
                        self.scan_names_tree(node[entry], entry)
            elif come_from == 'Dests':
                if 'Kids' in node:
                    for kid in node['Kids']:
                        self.scan_names_tree(kid, come_from)
                elif 'Names' in node:
                    nlist = node['Names']
                    while (len(nlist) >= 2) \
                    and (type(nlist[0]) == types.StringType) \
                    and (nlist[1].__class__ == PDFref):
                        self.scan_names_tree(nlist[1], come_from, nlist[0])
                        del nlist[:2]
                elif name and ('D' in node):
                    page = self.dest2page(node['D'])
                    if page:
                        self.names[name] = page
            # else: unsupported node, don't care
        except PDFError:
            self.errors += 1

    def dest2page(self, dest):
        if type(dest) in (types.StringType, types.UnicodeType):
            return self.names.get(dest, None)
        if type(dest) != types.ListType:
            return dest
        elif dest[0].__class__ == PDFref:
            return self.obj2page.get(dest[0].ref, None)
        else:
            return dest[0]

    def get_href(self, obj):
        try:
            node = self.getobj(obj, 'Annot')
            if node['Subtype'] != 'Link': return None
            dest = None
            if 'Dest' in node:
                dest = self.dest2page(node['Dest'])
            elif 'A' in node:
                a = node['A']
                if isinstance(a, PDFref):
                    a = self.getobj(a)
                action = a['S']
                if action == 'URI':
                    dest = a.get('URI', None)
                elif action == 'Launch':
                    dest = a.get('F', None)
                elif action == 'GoTo':
                    dest = self.dest2page(a.get('D', None))
            if dest:
                return tuple(node['Rect'] + [dest])
        except PDFError:
            self.errors += 1

    def GetHyperlinks(self):
        res = {}
        for page in self.annots:
            try:
                a = filter(None, map(self.get_href, self.annots[page]))
            except (PDFError, TypeError, ValueError):
                self.errors += 1
                a = None
            if a: res[page] = a
        return res


def rotate_coord(x, y, rot):
    if   rot == 1: x, y = 1.0 - y,       x
    elif rot == 2: x, y = 1.0 - x, 1.0 - y
    elif rot == 3: x, y =       y, 1.0 - x
    return (x, y)


def AddHyperlink(page_offset, page, target, linkbox, pagebox, rotate):
    page += page_offset
    if type(target) == types.IntType:
        target += page_offset

    # compute relative position of the link on the page
    w = 1.0 / (pagebox[2] - pagebox[0])
    h = 1.0 / (pagebox[3] - pagebox[1])
    x0 = (linkbox[0] - pagebox[0]) * w
    y0 = (pagebox[3] - linkbox[3]) * h
    x1 = (linkbox[2] - pagebox[0]) * w
    y1 = (pagebox[3] - linkbox[1]) * h

    # get effective rotation
    rotate /= 90
    page_rot = GetPageProp(page, 'rotate')
    if page_rot is None:
        page_rot = Rotation
    if page_rot:
        rotate += page_rot
    while rotate < 0:
        rotate += 1000000
    rotate &= 3

    # rotate the rectangle
    x0, y0 = rotate_coord(x0, y0, rotate)
    x1, y1 = rotate_coord(x1, y1, rotate)
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0

    # save the hyperlink
    href = (0, target, x0, y0, x1, y1)
    if GetPageProp(page, '_href'):
        PageProps[page]['_href'].append(href)
    else:
        SetPageProp(page, '_href', [href])


def FixHyperlinks(page):
    if not(GetPageProp(page, '_box')) or not(GetPageProp(page, '_href')):
        return  # no hyperlinks or unknown page size
    bx0, by0, bx1, by1 = GetPageProp(page, '_box')
    bdx = bx1 - bx0
    bdy = by1 - by0
    href = []
    for fixed, target, x0, y0, x1, y1 in GetPageProp(page, '_href'):
        if fixed:
            href.append((1, target, x0, y0, x1, y1))
        else:
            href.append((1, target, \
                int(bx0 + bdx * x0), int(by0 + bdy * y0), \
                int(bx0 + bdx * x1), int(by0 + bdy * y1)))
    SetPageProp(page, '_href', href)


def ParsePDF(filename):
    try:
        assert 0 == spawn(os.P_WAIT, pdftkPath, \
                ["pdftk", FileNameEscape + filename + FileNameEscape, \
                 "output", FileNameEscape + TempFileName + ".pdf" + FileNameEscape,
                 "uncompress"])
    except OSError:
        print >>sys.stderr, "Note: pdftk not found, hyperlinks disabled."
        return
    except AssertionError:
        print >>sys.stderr, "Note: pdftk failed, hyperlinks disabled."
        return

    count = 0
    try:
        try:
            pdf = PDFParser(TempFileName + ".pdf")
            for page, annots in pdf.GetHyperlinks().iteritems():
                for page_offset in FileProps[filename]['offsets']:
                    for a in annots:
                        AddHyperlink(page_offset, page, a[4], a[:4], pdf.box[page], pdf.rotate[page])
                count += len(annots)
                FixHyperlinks(page)
            if pdf.errors:
                print >>sys.stderr, "Note: there are errors in the PDF file, hyperlinks might not work properly"
            del pdf
            return count
        except IOError:
            print >>sys.stderr, "Note: file produced by pdftk not readable, hyperlinks disabled."
        except PDFError, e:
            print >>sys.stderr, "Note: error in PDF file, hyperlinks disabled."
            print >>sys.stderr, "      PDF parser error message:", e
    finally:
        try:
            os.remove(TempFileName + ".pdf")
        except OSError:
            pass
