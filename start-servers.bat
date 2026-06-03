@echo off
REM start-servers.bat — bring up the entire paper-pipeline stack.
REM ============================================================
REM
REM Opens up to three PowerShell windows, one per server, and tees each
REM window's combined stdout+stderr to a per-server log under logs\. A
REM future Claude Code session can read those logs to diagnose without
REM having to find the right window.
REM
REM THREE WINDOWS, THREE ERAS:
REM
REM   1. paper-coach     C# MCP server on :6000
REM      The new pipeline. Hosts the MCP tools the director skill calls
REM      (list_papers, extract, render_audio, etc.) and the C# rendering
REM      of script.json -> WAV via the shared TTS library.
REM      See SKILLS-PLAN.md section 2.1.
REM
REM   2. pdf-sidecar     Python FastAPI on :6001     [NOT YET IMPLEMENTED]
REM      Will own PDF -> Markdown extraction (pymupdf4llm / marker-pdf).
REM      Stub is below, commented out. paper-coach calls it over HTTP.
REM      See SKILLS-PLAN.md section 2.2.
REM
REM   3. legacy player   Python on :8847
REM      The old pipeline's web UI (podcast_player.html + state/manifest
REM      endpoints in server.py at the repo root — NOT the new C# server).
REM      Currently the only working way to audition generated audio for
REM      papers already processed under the legacy pipeline. Stays alive
REM      until the new reader UI lands. See SKILLS-PLAN.md section 10
REM      for the migration / deprecation plan.
REM
REM CONSOLIDATION NOTE (2026-06-02):
REM Previously this repo had two launchers: start_server.bat (legacy
REM Python player) and start-servers.bat (new C# server). The names
REM differed only by hyphen-vs-underscore and a plural 's'; a footgun
REM with no upside. Consolidated into this one file; both eras now
REM start from a single `start-servers.bat` invocation. When the new
REM reader UI lands and the legacy player retires, delete Window 3.
REM
REM WHY THE `cmd /c '... 2>&1'` WRAPPER:
REM   Windows PowerShell 5.1 wraps every line of a native command's
REM   stderr as a NativeCommandError when the PS pipeline does the 2>&1
REM   merge. Uvicorn/dotnet/python all log to stderr; a plain
REM   `python server.py 2>&1 | Tee-Object` sprays "RemoteException"
REM   frames into the log for every INFO line. Doing the merge inside
REM   cmd hands PowerShell a single already-merged byte stream, which
REM   Tee-Object writes cleanly. Lesson borrowed from the sibling
REM   ../ai-verbal-coaching/start-servers.bat (Voice Coach DEV-LOG
REM   2026-05-07).
REM
REM PYTHONUNBUFFERED=1
REM   Python full-buffers stdout when stdout isn't a TTY (i.e., when
REM   piped). Without this, log lines arrive in 4 KB chunks or never.
REM   Required for both pdf-sidecar (when it lands) and the legacy
REM   player.
REM
REM PAPER_COACH_ROOT
REM   The C# server uses this env var to find papers/, input/, and
REM   output/ regardless of which directory dotnet was invoked from.
REM   Kept even though we Set-Location into server\, because
REM   Set-Location is a parser-level choice while the env var is the
REM   runtime contract.

setlocal

REM This script lives at the repo root, so %~dp0 is the project dir.
set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

if not exist "%REPO_ROOT%\logs" mkdir "%REPO_ROOT%\logs"

REM -- Window 1 --- paper-coach C# MCP server ----------------------------
start "paper-coach :6000" powershell -NoExit -Command ^
  "$env:PAPER_COACH_ROOT='%REPO_ROOT%'; Set-Location '%REPO_ROOT%\server'; & cmd /c 'dotnet run 2>&1' | Tee-Object -FilePath '%REPO_ROOT%\logs\paper-coach.log'"

REM -- Window 2 --- pdf-sidecar Python FastAPI ---------------------------
REM .venv path matches SKILLS-PLAN.md section 1 and the bootstrap step
REM `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`
REM that brings it up first time. PAPER_COACH_ROOT is also exported so the
REM sidecar resolves repo-relative paths the same way paper-coach does.
start "pdf-sidecar :6001" powershell -NoExit -Command ^
  "$env:PYTHONUNBUFFERED='1'; $env:PAPER_COACH_ROOT='%REPO_ROOT%'; Set-Location '%REPO_ROOT%\pdf-sidecar'; & cmd /c '.\.venv\Scripts\python.exe -m uvicorn server:app --port 6001 --reload 2>&1' | Tee-Object -FilePath '%REPO_ROOT%\logs\pdf-sidecar.log'"

REM -- Window 3 --- legacy podcast player Python (port 8847) -------------
REM Old pipeline; serves podcast_player.html + manifest/state from the
REM repo-root server.py. Port + bind addr are decided inside server.py.
start "legacy player :8847" powershell -NoExit -Command ^
  "$env:PYTHONUNBUFFERED='1'; Set-Location '%REPO_ROOT%'; & cmd /c 'python server.py 2>&1' | Tee-Object -FilePath '%REPO_ROOT%\logs\legacy-player.log'"

echo.
echo Servers launching in separate PowerShell windows.
echo   paper-coach     http://localhost:6000/mcp     log: logs\paper-coach.log
echo   pdf-sidecar     http://localhost:6001         log: logs\pdf-sidecar.log
echo   legacy player   http://localhost:8847         log: logs\legacy-player.log
echo.
echo Probes:
echo   curl http://localhost:6000/api/health         paper-coach
echo   curl http://localhost:6001/api/health         pdf-sidecar
echo   curl http://localhost:8847                    legacy player

endlocal
