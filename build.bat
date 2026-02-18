@echo off
echo Compiling TelegramUnblocker...

if not exist "bin" mkdir bin

pyinstaller --onefile --uac-admin --hidden-import=win32timezone --hidden-import=servicemanager --distpath bin --workpath build --specpath build TelegramUnblocker.py

echo.
echo [OK] Done!
echo     Executable: bin\TelegramUnblocker.exe
echo     Manager:    Manage.bat
pause
