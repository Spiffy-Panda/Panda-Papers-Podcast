@echo off
echo Stopping server on port 8847...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8847 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a
)
echo Done.
pause
