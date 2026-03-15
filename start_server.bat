@echo off
title Podcast Server (port 8847 - LAN)
cd /d "%~dp0"
echo Starting server on LAN (0.0.0.0:8847)...
echo.
echo   If Windows Firewall prompts, click Allow to enable LAN access.
echo.
python server.py
pause
