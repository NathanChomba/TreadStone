@echo off
rem Treadstone: start the Django API, the Django-Q worker and the Vite PWA, then open the app.
rem Double-click this file. Close the terminal window (or its tabs) to stop everything.

setlocal
set ROOT=%~dp0
set PY=%ROOT%backend\venv\Scripts\python.exe

if not exist "%PY%" (
  echo Could not find the virtual environment at backend\venv. Create it first.
  pause
  exit /b 1
)

where wt.exe >nul 2>nul
if %errorlevel%==0 (
  rem One Windows Terminal window, three tabs.
  wt.exe -w new ^
    new-tab --title "API :8000" -d "%ROOT%backend" cmd /k venv\Scripts\python.exe manage.py runserver ^
    ; new-tab --title "Worker" -d "%ROOT%backend" cmd /k venv\Scripts\python.exe manage.py qcluster ^
    ; new-tab --title "PWA :5173" -d "%ROOT%frontend" cmd /k npm run dev
) else (
  rem No Windows Terminal: three separate console windows.
  start "Treadstone API :8000" /d "%ROOT%backend" cmd /k venv\Scripts\python.exe manage.py runserver
  start "Treadstone Worker" /d "%ROOT%backend" cmd /k venv\Scripts\python.exe manage.py qcluster
  start "Treadstone PWA :5173" /d "%ROOT%frontend" cmd /k npm run dev
)

rem Give the servers a few seconds to come up, then open the app.
timeout /t 6 /nobreak >nul
start "" http://localhost:5173
endlocal
