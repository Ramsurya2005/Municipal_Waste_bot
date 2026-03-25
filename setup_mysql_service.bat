@echo off
REM MySQL Quick Setup Script for Municipal Chatbot

echo ========================================
echo MySQL Server Configuration
echo ========================================
echo.

REM Set MySQL paths
set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.4\bin
set MYSQL_DATA=C:\ProgramData\MySQL\MySQL Server 8.4\Data

echo Step 1: Adding MySQL to PATH...
setx PATH "%PATH%;%MYSQL_BIN%" >nul 2>&1

echo Step 2: Checking MySQL service...
sc query MySQL84 >nul 2>&1
if %errorlevel% neq 0 (
    echo MySQL service not found. Installing service...
    "%MYSQL_BIN%\mysqld.exe" --install MySQL84
    echo Service installed.
)

echo Step 3: Starting MySQL service...
net start MySQL84

echo.
echo ========================================
echo MySQL is now running!
echo ========================================
echo.
echo Default connection details:
echo   Host: localhost
echo   Port: 3306
echo   User: root
echo   Password: (initially empty, you'll set it next)
echo.
echo IMPORTANT: You need to set a root password.
echo.
echo Run this command to set password (replace 'YourPassword' with your choice):
echo   mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourPassword';"
echo.
echo Then update your .env file with:
echo   MYSQL_PASSWORD=YourPassword
echo.
pause
