@echo off
rem Treadstone: import ~2.7 years (from March 2024) of REAL daily gold and silver prices (GoldAPI + real USD->ZMW rates)
rem and remove the old simulated prices. Safe to run again any time. Takes a minute or two.

setlocal
cd /d "%~dp0backend"
if not exist "venv\Scripts\python.exe" (
  echo Could not find the virtual environment at backend\venv.
  pause
  exit /b 1
)
venv\Scripts\python.exe manage.py import_price_history --days 980 --replace
echo.
pause
endlocal
