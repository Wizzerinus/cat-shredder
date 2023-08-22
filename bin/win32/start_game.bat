@echo off
title Cat Shredder Game Client

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH
cd ../..

echo Cat Shredder - Connect to server

set /P TT_PLAYCOOKIE="Username (default: dev): " || ^
set TT_PLAYCOOKIE=dev

set /P TT_GAMESERVER="Game Server (default: 127.0.0.1): " || ^
set TT_GAMESERVER=127.0.0.1

%PPYTHON_PATH% -m toontown.toonbase.ToontownStart
pause
