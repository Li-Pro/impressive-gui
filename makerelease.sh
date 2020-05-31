#!/bin/bash

make all

base=_releases
dir=Impressive
exe=impressive.py
hlp=site/impressive.html
if [ -z "$1" ] ; then
    dir=$dir-$(grep __version__ $exe | head -n 1 | cut -d'"' -f2)
elif [ "$1" != "--noversion" ] ; then
    dir=$dir-$1
fi

rm -rf $base/$dir
mkdir -p $base/$dir
chmod -x demo.pdf
cp demo.pdf $base/$dir
cp impressive $base/$dir/
for file in $exe $hlp license.txt changelog.txt impressive.1 ; do
  tr -d '\r' <$file >$base/$dir/$(basename $file)
done

cd $base
rm -f $dir.tar.gz
tar czvf $dir.tar.gz $dir/
