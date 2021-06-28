@echo off

python compile.py
if errorlevel 1 goto end

python win32\get_version_info.py impressive.py >win32_version.txt
if errorlevel 1 goto end

@rem clean up; in particular the PyInstaller cache may incur hard-to-debug issues
rmdir /s /q %AppData%\pyinstaller
rmdir /s /q build
rmdir /s /q dist

python -m PyInstaller ^
    --noconfirm --onedir --console --name=Impressive ^
    --icon=Artwork\icon.ico --version-file=win32_version.txt ^
    --exclude-module Tkinter ^
    --exclude-module scipy ^
    --exclude-module numpy ^
    --exclude-module lib2to3 ^
    --upx-exclude vcruntime140.dll ^
	--windowed ^
    impressive.py
if errorlevel 1 goto end
rmdir /s /q build
del dist\Impressive\Impressive.exe.manifest
del Impressive.spec
del logdict2.*.log
del win32_version.txt

set target=dist\Impressive\
copy /b win32\*.exe %target%
copy /b win32\*.dll %target%
copy /b demo.pdf %target%
copy /b license.txt %target%
copy /b changelog.txt %target%
copy /b site\Impressive.html %target%\Impressive_Documentation.html

del Impressive.zip
cd %target%

:: zip -r9 ..\..\Impressive.zip .
python ..\..\makedist_zipdir.py ..\..\Impressive.zip .

cd ..\..

:end