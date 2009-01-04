#!/usr/bin/env python

PROJECT_NAME = "impressive"
IN_FILE_NAME = PROJECT_NAME + "_dev.py"
OUT_FILE_NAME = PROJECT_NAME + ".py"

import re
re_exec = re.compile('\s*execfile\s*\(\s*[\'"](.*?)[\'"]\s*,\s*globals\s*\(\s*\)\s*\)\s*$')

out = open(OUT_FILE_NAME, "wb")
was_include = False
for line in open(IN_FILE_NAME, "r"):
    m = re_exec.match(line)
    if m:
        if was_include: out.write("\n\n")
        print m.group(1)
        out.write(open(m.group(1), "rb").read().replace("\r\n", "\n").strip("\n") + "\n")
    else:
        out.write(line.replace("\r\n", "\n"))
    was_include = not(not(m))
out.close()
