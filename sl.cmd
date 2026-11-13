@echo off
rem SpiderLab server helper - Windows entry point.
rem Real logic lives in sl.sh; this just launches it with Git Bash.
setlocal
set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if exist "%BASH_EXE%" goto run
set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
if exist "%BASH_EXE%" goto run
set "BASH_EXE=bash"
:run
"%BASH_EXE%" "%~dp0sl.sh" %*
