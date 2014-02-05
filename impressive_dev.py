#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Impressive, a fancy presentation tool
# Copyright (C) 2005-2010 Martin J. Fiedler <martin.fiedler@gmx.net>
# portions Copyright (C) 2005 Rob Reid <rreid@drao.nrc.ca>
# portions Copyright (C) 2006 Ronan Le Hy <rlehy@free.fr>
# portions Copyright (C) 2007 Luke Campagnola <luke.campagnola@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__title__   = "Impressive"
__version__ = "0.10.4"
__rev__     = None
__author__  = "Martin J. Fiedler"
__email__   = "martin.fiedler@gmx.net"
__website__ = "http://impressive.sourceforge.net/"

import sys
if __rev__ and (("WIP" in __version__) or ("rc" in __version__) or ("alpha" in __version__) or ("beta" in __version__)):
    __version__ += " (SVN r%s)" % __rev__
def greet():
    print >>sys.stderr, "Welcome to", __title__, "version", __version__
if __name__ == "__main__":
    greet()


execfile("src/defaults.py", globals())
execfile("src/init.py", globals())
execfile("src/globals.py", globals())
execfile("src/tools.py", globals())
execfile("src/gltools.py", globals())
execfile("src/transitions.py", globals())
execfile("src/osdfont.py", globals())
execfile("src/pdfparse.py", globals())
execfile("src/cache.py", globals())
execfile("src/render.py", globals())
execfile("src/scriptwriter.py", globals())
execfile("src/gldraw.py", globals())
execfile("src/control.py", globals())
execfile("src/overview.py", globals())
execfile("src/event.py", globals())
execfile('src/filelist.py', globals())
execfile('src/main.py', globals())
execfile("src/options.py", globals())


# use this function if you intend to use Impressive as a library
def run():
    try:
        run_main()
    except SystemExit, e:
        return e.code

if __name__ == "__main__":
    try:
        ParseOptions(sys.argv[1:])
        run_main()
    finally:
        if not(CleanExit) and (os.name == 'nt') and getattr(sys, "frozen", False):
            print
            raw_input("<-- press ENTER to quit the program --> ")
