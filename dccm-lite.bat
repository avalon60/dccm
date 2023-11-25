::##############################################################################
::# Author: Clive Bostock
::#   Date: 1 Jul 2023 (A Merry Christmas to one and all! :o)
::#   Name: dccm.sh
::#  Descr: Database Client Connection Manager (dccm-lite)
::##############################################################################
@echo off
set PROG_PATH="%~dp0"
set APP_ENV=%PROG_PATH%\venv
call %APP_ENV%\Scripts\activate.bat
%PROG_PATH%\dccm-lite.py %1 %2 %3 %4 %5 %6
