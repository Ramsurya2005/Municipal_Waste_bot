@echo off
:: Run as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

cls
echo ============================================================
echo  MySQL Setup and Migration - Municipal Chatbot
echo ============================================================
echo.

:: Step 1: Start MySQL Service
echo [1/3] Starting MySQL Service...
net start MySQL84 2>nul
if %errorlevel% equ 0 (
    echo       ✅ MySQL service started
) else (
    echo       ✅ MySQL service already running
)
echo.

:: Wait for MySQL to initialize
timeout /t 3 /nobreak >nul

:: Step 2: Create Database and Tables
echo [2/3] Creating Database...
cd /d "%~dp0"
venv\Scripts\python.exe setup_mysql.py
echo.

:: Step 3: Migrate Data from SQLite
echo [3/3] Migrating Data from SQLite to MySQL...
venv\Scripts\python.exe migrate_sqlite_to_mysql.py
echo.

echo ============================================================
echo  Setup Complete!
echo ============================================================
echo.
echo Your application is now using MySQL database.
echo You can run: streamlit run app.py
echo.
pause
