@echo off
set FLAG=C:\RGB_boot_flag.txt

:: check if the flag already exists, so the script only runs once
if not exist "%FLAG%" exit

:: you can change the timeout if your computer takes longer to load your device's applications
timeout /t 20 /nobreak
start "" "C:\projects\RGBController\RGBController.exe"

:: this consumes the flag so we don't start the program again on this boot
del "%FLAG%"
