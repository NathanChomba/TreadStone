@echo off
rem One-time setup: let a phone on the same Wi-Fi reach the Treadstone dev server (port 5173).
rem Double-click it and press "Yes" on the Windows permission prompt.

net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

powershell -NoProfile -Command ^
  "if (Get-NetFirewallRule -DisplayName 'Treadstone dev (port 5173)' -ErrorAction SilentlyContinue) { 'Rule already exists - nothing to do.' } else { New-NetFirewallRule -DisplayName 'Treadstone dev (port 5173)' -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow -Profile Any | Out-Null; 'Firewall rule added: port 5173 is open for your phone.' }"

echo.
echo Your PC's Wi-Fi address(es) - open http://ADDRESS:5173 on your phone:
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254*' } | ForEach-Object { '   http://' + $_.IPAddress + ':5173' }"
echo.
pause
