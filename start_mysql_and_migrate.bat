@echo off
echo ========================================
echo Starting MySQL and Running Migration
echo ========================================
echo.

REM Start MySQL service
echo Step 1: Starting MySQL service...
net start MySQL84
if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to start MySQL service
    echo 💡 This script needs to run as Administrator
    echo.
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo ✅ MySQL service started
echo.

REM Wait a moment for MySQL to fully start
timeout /t 2 /nobreak >nul

REM Run setup script
echo Step 2: Creating database...
cd /d "%~dp0"
venv\Scripts\python.exe setup_mysql.py

if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Database setup encountered an issue
    echo 💡 You may need to set MySQL root password first
    pause
    exit /b 1
)

echo.
echo Step 3: Running data migration...
venv\Scripts\python.exe migrate_sqlite_to_mysql.py

echo.
echo ========================================
echo ✅ All done!
echo ========================================
echo.
pause
