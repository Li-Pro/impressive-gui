#!/usr/bin/env python

from __future__ import print_function
import codecs

def execfile(f, c):
    with open(f) as h:
        code = compile(h.read(), f, 'exec')
        exec(code, c)

Assets = [
    ("logo.png", "LOGO"),
    ("cursor.png", "DEFAULT_CURSOR")
]

if __name__ == "__main__":
    contents = {}
    f = open("assets.tmp.py", "w")
    for filename, varname in Assets:
        print("encoding %s into %s ..." % (filename, varname))
        contents[filename] = open(filename, "rb").read()
        data = codecs.encode(contents[filename], 'base64').decode().replace('\n', '')
        brk = 247 - len(varname)
        while brk < len(data):
            data = data[:brk] + "\r\n" + data[brk:]
            brk += 256
        f.write('%s = b"""%s"""\r\n' % (varname, data))
    f.close()

    execfile("assets.tmp.py", globals())

    for filename, varname in Assets:
        print("verifying %s ..." % varname, end=' ')
        data = codecs.decode(globals()[varname], 'base64')
        if data == contents[filename]:
            print("OK")
        else:
            print("FAILED")
