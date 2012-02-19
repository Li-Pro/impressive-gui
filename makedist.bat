@echo off
set PY=C:\Programme\Dev\Python25\Lib

rm -rfv dist

python deploy.py py2exe --excludes=OpenGL
if errorlevel 1 goto end

rem cp -a gs dist
cp -a OpenGL dist
rm -rf build
cp license.txt dist
cp changelog.txt dist
cp site/impressive.html dist
cp demo.pdf dist
cp msvcr71.dll dist
cp *.exe dist

rm -f Impressive.zip
cd dist
rm -rf tcl tcl*.dll tk*.dll
zip -rv9 ..\Impressive *
cd ..

du -hs dist Impressive.zip

:end