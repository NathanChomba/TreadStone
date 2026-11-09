@echo off
rem Treadstone: rebuild the five-member defense demo from real historical gold prices.
rem Safe to run any time - it removes only the demo members and their group, then recreates them.
setlocal
cd /d "%~dp0backend"
if not exist "venv\Scripts\python.exe" (
  echo Could not find the virtual environment at backend\venv.
  pause
  exit /b 1
)
venv\Scripts\python.exe manage.py seed_demo --reset
echo.
pause
endlocal
