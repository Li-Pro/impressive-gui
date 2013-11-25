#!/usr/bin/env python

PROJECT_NAME = "impressive"
IN_FILE_NAME = PROJECT_NAME + "_dev.py"
OUT_FILE_NAME = PROJECT_NAME + ".py"

import sys, re, os, stat, subprocess
re_rev = re.compile(r'\s*__rev__\s*=\s*(None|\d+|"[^"]*"|\'[^\']*\')\s*$')
re_exec = re.compile(r'\s*execfile\s*\(\s*[\'"](.*?)[\'"]\s*,\s*globals\s*\(\s*\)\s*\)\s*$')

out = open(OUT_FILE_NAME, "wb")
was_include = False
for line in open(IN_FILE_NAME, "r"):
    m = re_rev.match(line)
    if m:
        try:
            os.environ["LC_MESSAGES"] = "C"
            rev, err = subprocess.Popen(["svnversion"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if err:
                raise RuntimeError(err.strip())
            if rev.strip().lower() == "exported":
                raise RuntimeError("not a working copy")
            rev = max([int(r.strip("SMP \r\n\t\f\v")) for r in rev.split(':')])
            line = line[:m.start(1)] + str(rev) + line[m.end(1):]
            print "SVN revision:", rev
        except Exception, e:
            print >>sys.stderr, "WARNING: could not get SVN revision -", e
    m = re_exec.match(line)
    if m:
        if was_include: out.write("\n\n")
        print m.group(1)
        out.write(open(m.group(1), "rb").read().replace("\r\n", "\n").strip("\n") + "\n")
    else:
        out.write(line.replace("\r\n", "\n"))
    was_include = not(not(m))
out.close()

try:
    s = os.stat(OUT_FILE_NAME)
    os.chmod(OUT_FILE_NAME, s.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
except (OSError, AttributeError):
    pass
