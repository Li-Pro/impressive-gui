The following files have to be present in this directory in order to build the
Win32 executables of Impressive:

* pdftk.exe - an older version of pdftk (<= 1.45). original source:
              http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/
              Note: may also require libiconv2.dll

* mutool.exe - MuPDF rendering tool (optimal version, size-wise: 1.8)
               https://mupdf.com/downloads/archive/

* mplayer.exe - any 32-bit Windows build of MPlayer or MPlayer2, for example:
                http://mplayerwin.sourceforge.net/downloads.html

+ any special DLLs your Python version requires;
  for Python 2.5, for example, that's msvcr71.dll
