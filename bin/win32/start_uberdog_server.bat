@echo off
title Cat Shredder - UberDOG server

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH
cd ../..

:main
%PPYTHON_PATH% -m toontown.uberdog.UDStart
goto main
