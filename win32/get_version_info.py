#!/usr/bin/head -n 2
# This tool is useful on Win32 only.
import sys, re

if __name__ == "__main__":
    info = dict(re.findall(r'^__(.*?)__\s*=\s*"(.*?)"', open(sys.argv[1]).read(), re.M))
    version = tuple((map(int, re.findall(r'\d+', info['version'])) + [0, 0, 0, 0])[:4])
    print "VSVersionInfo("
    print "  ffi=FixedFileInfo("
    print "    filevers=%r," % (version,)
    print "    prodvers=%r," % (version,)
    print "    mask=0x0,"
    print "    flags=0x0,"
    print "    OS=0x4,"
    print "    fileType=0x1,"
    print "    subtype=0x0,"
    print "    date=(0, 0)"
    print "    ),"
    print "  kids=["
    print "    StringFileInfo("
    print "      ["
    print "      StringTable("
    print "        u'000004b0',"
    print "        [StringStruct(u'CompanyName', %r)," % unicode(info['author'])
    print "        StringStruct(u'FileDescription', %r)," % unicode(info['title'])
    print "        StringStruct(u'FileVersion', %r)," % unicode(info['version'])
    print "        StringStruct(u'OriginalFilename', %r)," % unicode(sys.argv[1])
    print "        StringStruct(u'ProductName', %r)," % unicode(info['title'])
    print "        StringStruct(u'ProductVersion', %r)])" % unicode(info['version'])
    print "      ]),"
    print "    VarFileInfo([VarStruct(u'Translation', [0, 1200])])"
    print "  ]"
    print ")"