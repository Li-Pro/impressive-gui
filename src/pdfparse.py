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

        # scan the page tree
        self.obj2page = {}
        self.page2obj = {}
        self.annots = {}
        self.page_count = 0
        self.box = {}
        root = self.getobj(rootref, 'Catalog')
        try:
            self.scan_page_tree(root['Pages'].ref)
        except KeyError:
            raise PDFError, "root page tree node missing"

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
        data = data.replace("/", " /")
        return self.parse_tokens(filter(None, data.split()))

    def getobj(self, obj, force_type=None):
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
        while True:
            line = self.getline()
            if line in ("startxref", "%%EOF"): break
            if line[0] != '/': continue
            parts = line[1:].split()
            if parts[0] == 'Prev':
                offset = int(parts[1])
            if parts[0] == 'Root':
                if (len(parts) != 4) or (parts[3] != 'R'):
                    raise PDFError, "root catalog entry is not a reference"
                rootref = int(parts[1])
        return (xref, rootref, offset)

    def scan_page_tree(self, obj, mbox=None, cbox=None):
        node = self.getobj(obj)
        if node['Type'] == 'Pages':
            for kid in node['Kids']:
                self.scan_page_tree(kid.ref, node.get('MediaBox', mbox), node.get('CropBox', cbox))
        else:
            page = self.page_count + 1
            anode = node.get('Annots', [])
            if anode.__class__ == PDFref:
                anode = self.getobj(anode.ref)
            self.page_count = page
            self.obj2page[obj] = page
            self.page2obj[page] = obj
            self.annots[page] = [a.ref for a in anode]
            self.box[page] = node.get('CropBox', cbox) or node.get('MediaBox', mbox)

    def dest2page(self, dest):
        if type(dest) != types.ListType:
            return dest
        elif dest[0].__class__ == PDFref:
            return self.obj2page.get(dest[0].ref, None)
        else:
            return dest[0]

    def get_href(self, obj):
        node = self.getobj(obj, 'Annot')
        if node['Subtype'] != 'Link': return None
        dest = None
        if 'Dest' in node:
            dest = self.dest2page(node['Dest'])
        elif 'A' in node:
            action = node['A']['S']
            if action == 'URI':
                dest = node['A'].get('URI', None)
            elif action == 'GoTo':
                dest = self.dest2page(node['A'].get('D', None))
        if dest:
            return tuple(node['Rect'] + [dest])

    def GetHyperlinks(self):
        res = {}
        for page in self.annots:
            a = filter(None, map(self.get_href, self.annots[page]))
            if a: res[page] = a
        return res


def AddHyperlink(page_offset, page, target, linkbox, pagebox):
    page += page_offset
    if type(target) == types.IntType:
        target += page_offset
    w = 1.0 / (pagebox[2] - pagebox[0])
    h = 1.0 / (pagebox[3] - pagebox[1])
    x0 = (linkbox[0] - pagebox[0]) * w
    y0 = (pagebox[3] - linkbox[3]) * h
    x1 = (linkbox[2] - pagebox[0]) * w
    y1 = (pagebox[3] - linkbox[1]) * h
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
                        AddHyperlink(page_offset, page, a[4], a[:4], pdf.box[page])
                count += len(annots)
                FixHyperlinks(page)
            del pdf
            return count
        except IOError:
            print >>sys.stderr, "Note: file produced by pdftk not readable, hyperlinks disabled."
        except PDFError, e:
            print >>sys.stderr, "Note: error in file produced by pdftk, hyperlinks disabled."
            print >>sys.stderr, "      PDF parser error message:", e
    finally:
        try:
            os.remove(TempFileName + ".pdf")
        except OSError:
            pass
