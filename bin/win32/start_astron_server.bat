@echo off
title Cat Shredder - Astron Server
cd ../../dependencies
astrond.exe --loglevel info ../etc/cluster.yml
pause
