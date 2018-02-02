#!/bin/sh
# see: https://github.com/philipl/mplayer/blob/master/DOCS/tech/crosscompile.txt
# see: https://wiki.openttd.org/Cross-compiling_for_Windows
# note 1: this script only works on Debian and Ubuntu without modifications
# note 2: this will pollute some directories that belong to the package manager

MPLAYER_VERSION=1.3.0
ZLIB_VERSION=1.2.11
PARALLEL_BUILDS=-j4
LIB_INSTALL_PREFIX=/usr/i686-w64-mingw32

set -ex

which yasm i686-w64-mingw32-gcc || sudo apt install mingw-w64 yasm

test -d crossbuild || mkdir crossbuild
cd crossbuild

if [ ! -f $LIB_INSTALL_PREFIX/include/zlib.h -o ! -f $LIB_INSTALL_PREFIX/lib/libz.a ] ; then
    test -d zlib-$ZLIB_VERSION/ || wget -qO- http://zlib.net/zlib-$ZLIB_VERSION.tar.gz | tar xzv
    cd zlib-$ZLIB_VERSION/
    sed -e s/"PREFIX =.*"/"PREFIX = i686-w64-mingw32-"/ -i win32/Makefile.gcc
    make -f win32/Makefile.gcc
    sudo BINARY_PATH=$LIB_INSTALL_PREFIX/bin \
        INCLUDE_PATH=$LIB_INSTALL_PREFIX/include \
        LIBRARY_PATH=$LIB_INSTALL_PREFIX/lib \
        make -f win32/Makefile.gcc install
    cd ..
fi

test -d MPlayer-$MPLAYER_VERSION/ || wget -qO- http://mplayerhq.hu/MPlayer/releases/MPlayer-$MPLAYER_VERSION.tar.xz | tar xJv
cd MPlayer-$MPLAYER_VERSION/
make distclean || true
# force-disable all encoders, even those that are enabled unconditionally
sed -r -e 's/^(libav(encoders|filters)=)\$\(echo.*/\1/' -e 's/(.*MPEG1VIDEO_ENC)/true #\1/' -i configure
./configure \
    --enable-cross-compile --windres=i686-w64-mingw32-windres --cc=i686-w64-mingw32-gcc \
    --enable-runtime-cpudetection --enable-static --disable-mencoder \
    --disable-tv --disable-ftp \
    --disable-qtx --disable-real --disable-win32dll \
    --disable-matrixview --disable-direct3d --disable-md5sum --disable-tga \
    --disable-decoder=metasound --disable-decoder=twinvq \
    --disable-decoder=tiff --disable-decoder=hq_hqa --disable-decoder=ralf
time nice make $PARALLEL_BUILDS
cp mplayer.exe ../..
cd ..

cd ..
ls -l mplayer.exe
