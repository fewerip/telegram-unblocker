@echo off
cd /d "%~dp0"
set "BIN=bin\TelegramUnblocker.exe"
set "SERVICE_NAME=TelegramUnblocker"

:: --- Auto-Jump Logic ---
if "%1"=="jump_install" goto install
if "%1"=="jump_remove" goto remove

:menu
cls
echo ===========================================
echo   TELEGRAM UNBLOCKER (Fragmented Proxy)
echo ===========================================
if exist "bin\config.json" echo   [Status] Config found.
if not exist "bin\config.json" echo   [Status] No config found.
echo.
echo   1. Configure Proxy
echo   2. Test Run (Console)
echo   3. Install Service (Auto-Start)
echo   4. Remove Service
echo   5. How to Setup Telegram (Guide)
echo   6. Exit
echo.
set /p c=Select Option: 

if "%c%"=="1" goto configure
if "%c%"=="2" goto testrun
if "%c%"=="3" goto install
if "%c%"=="4" goto remove
if "%c%"=="5" goto guide
if "%c%"=="6" exit
goto menu

:guide
cls
echo ==================================================
echo         HOW TO SETUP TELEGRAM PROXY
echo ==================================================
echo.
echo 1. Open Telegram Desktop.
echo 2. Go to Settings (Three bars top left - Settings).
echo 3. Click "Data and Storage".
echo 4. Scroll down to "Connection Type" / "Proxy Settings".
echo 5. Click "Add Proxy".
echo 6. Choose "SOCKS5".
echo.
echo    Socket Address (Host):  127.0.0.1
echo    Port:                   10805 (Default) or your custom port
echo.
echo    Username/Password:      (Leave Empty)
echo.
echo 7. Click "Save".
echo.
echo ==================================================
echo.
pause
goto menu

:configure
cls
if not exist "%BIN%" (
    echo [!] Error: %BIN% not found. Please build first.
    pause
    goto menu
)
"%BIN%" --configure
pause
goto menu

:testrun
cls
echo [INFO] Running in console mode. Close window to stop.
"%BIN%" --test
pause
goto menu

:install
cls
:: Check Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Admin rights required. Restarting as Administrator...
    powershell -Command "Start-Process '%~f0' -ArgumentList 'jump_install' -Verb RunAs"
    goto menu
)

echo [INFO] Creating Service...
sc create %SERVICE_NAME% binPath= "%~dp0%BIN%" start= auto displayname= "Telegram Unblocker Service"
if %errorLevel% neq 0 (
    echo [X] Failed to create service.
    pause
    goto menu
)

echo [INFO] Setting failure actions (Restart on crash)...
sc failure %SERVICE_NAME% reset= 86400 actions= restart/5000/restart/5000/restart/5000

echo [INFO] Starting Service...
sc start %SERVICE_NAME%
echo.
echo [OK] Done. Service should be running.
pause
if "%1"=="jump_install" exit
goto menu

:remove
cls
:: Check Admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Admin rights required. Restarting as Administrator...
    powershell -Command "Start-Process '%~f0' -ArgumentList 'jump_remove' -Verb RunAs"
    goto menu
)

echo [INFO] Stopping Service...
sc stop %SERVICE_NAME%
echo [INFO] Deleting Service...
sc delete %SERVICE_NAME%
echo.
echo [OK] Service removed.
pause
if "%1"=="jump_remove" exit
goto menu
