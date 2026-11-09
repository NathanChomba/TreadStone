@echo off
rem Treadstone: five scripted agents use the real app in visible Edge windows, plus an admin window.
rem start.bat must already be running. The first run installs a small tool (needs internet once).
setlocal
cd /d "%~dp0demo"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. It is the same Node that runs the frontend - install it from nodejs.org.
  pause
  exit /b 1
)
if not exist "node_modules\playwright-core" (
  echo First run: installing the demo tool, one time only...
  call npm install --no-audit --no-fund
)
node agents.js
echo.
pause
endlocal
