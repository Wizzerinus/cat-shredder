@echo off

taskkill /f /im astrond.exe
taskkill /f /im ppython.exe
taskkill /f /fi "windowtitle eq Cat Shredder - UberDOG server"
taskkill /f /fi "windowtitle eq Cat Shredder - Astron Server"
taskkill /f /fi "windowtitle eq Cat Shredder - AI (District) server"
taskkill /f /fi "windowtitle eq Cat Shredder Game Client"

start start_astron_server.bat

ping 192.0.2.2 -n 1 -w 300 > nul
start start_uberdog_server.bat

ping 192.0.2.2 -n 1 -w 300 > nul
start start_ai_server.bat

ping 192.0.2.2 -n 1 -w 1500 > nul
start start_game.bat