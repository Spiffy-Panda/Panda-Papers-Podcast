@echo off
REM start-servers.bat — bring up the paper-coach pipeline.
REM   paper-coach   C# MCP server on :6000
REM   pdf-sidecar   Python FastAPI on :6001   (TODO: not yet implemented)
REM
REM Each server opens in its own PowerShell window and tees stdout to
REM logs\<name>.log so a future shell can `Get-Content -Wait logs\*.log`
REM without having to find the right window.

setlocal

REM This script lives at the repo root, so %~dp0 is the project dir.
set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

if not exist "%REPO_ROOT%\logs" mkdir "%REPO_ROOT%\logs"

REM PAPER_COACH_ROOT tells the C# server where to scan for papers/ and
REM input/ regardless of which directory dotnet was invoked from.
start "paper-coach :6000" powershell -NoExit -Command ^
  "$env:PAPER_COACH_ROOT='%REPO_ROOT%'; dotnet run --project '%REPO_ROOT%\server\PaperCoach.Server.csproj' 2>&1 | Tee-Object -FilePath '%REPO_ROOT%\logs\paper-coach.log'"

REM TODO: pdf-sidecar (Python FastAPI on :6001) once that exists.
REM start "pdf-sidecar :6001" powershell -NoExit -Command ^
REM   "cd '%REPO_ROOT%\pdf-sidecar'; .\.venv\Scripts\Activate.ps1; uvicorn server:app --port 6001 --reload 2>&1 | Tee-Object -FilePath '%REPO_ROOT%\logs\pdf-sidecar.log'"

echo.
echo Servers launching in separate PowerShell windows.
echo   paper-coach   http://localhost:6000/mcp    log: logs\paper-coach.log
echo   pdf-sidecar   (not yet implemented)
echo.
echo Probe paper-coach when ready:
echo   curl http://localhost:6000/api/health

endlocal
