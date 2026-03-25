@echo off
echo Starting MySQL Service...
net start MySQL84
if %errorlevel% equ 0 (
    echo.
    echo ✅ MySQL service started successfully!
    echo.
) else (
    echo.
    echo ❌ Failed to start MySQL
    echo Make sure you ran this as Administrator
    echo.
)
pause
