@echo off
set pyinstaller_path="C:\Program Files (x86)\Dev\Python25\pyinstaller-2.0"

python compile.py
if errorlevel 1 goto end

python %pyinstaller_path%\pyinstaller.py --noconfirm --onedir --name=Impressive --console impressive.py
if errorlevel 1 goto end
rmdir /s /q build
del Impressive.spec
del logdict2.*.log

set target=dist\Impressive\
copy /b win32\*.exe %target%
copy /b win32\*.dll %target%
copy /b demo.pdf %target%
copy /b license.txt %target%
copy /b changelog.txt %target%
copy /b site\Impressive.html %target%

del Impressive.zip
zip -jr9 Impressive.zip %target%

:end