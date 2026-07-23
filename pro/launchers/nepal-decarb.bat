@echo off
REM nepal-decarb launcher (Day 11). ROOT is computed from the .bat's location.
setlocal
set "BAT_DIR=%~dp0"
if "%BAT_DIR:~-1%"=="\" set "BAT_DIR=%BAT_DIR:~0,-1%"
REM Walk up from <dist> to find the repo root (looks for nepal-decarb-build or nepal_decarb_pro)
set "ROOT=%BAT_DIR%"
:findroot
if exist "%ROOT%\pro\src\nepal_decarb_pro\__init__.py" goto gotroot
if "%ROOT%"=="%ROOT:~0,3%" goto failroot
for %%P in ("%ROOT%") do set "ROOT=%%~dpP"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
goto findroot
:gotroot
set "PY_EXE=C:\Users\TG\AppData\Local\Programs\Python\Python312\python.exe"
set "PYTHONPATH=%ROOT%\pro\src;%ROOT%\tools\02-kiln-dynamics-simulator\src;%ROOT%\tools\03-cooler-grate-simulator\src;%PYTHONPATH%"
"%PY_EXE%" -m nepal_decarb_pro.cli %*
exit /b %ERRORLEVEL%
:failroot
echo [nepal-decarb] ERROR: could not find repo root from %BAT_DIR%
exit /b 1
