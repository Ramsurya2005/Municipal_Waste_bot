# MySQL Installation Guide for Windows

## Quick Installation Steps

### Method 1: MySQL Installer (Recommended)

1. **Download MySQL Installer**
   - Go to: https://dev.mysql.com/downloads/installer/
   - Download: `mysql-installer-community-8.0.xx.msi` (Web or Full)

2. **Run the Installer**
   - Choose Setup Type: **Developer Default** (recommended)
   - Or choose **Server Only** for minimal installation

3. **Configuration**
   - Server Configuration Type: **Development Computer**
   - Port: **3306** (default)
   - Authentication: **Use Strong Password Encryption**
   - Set ROOT password: Choose a strong password
   - Create Windows Service: **Yes** (auto-start MySQL)

4. **Complete Installation**
   - Execute all configuration steps
   - Finish and start MySQL service

### Method 2: Chocolatey (Quick Install)

```powershell
# Run PowerShell as Administrator
choco install mysql -y

# Start MySQL service
net start MySQL
```

### Method 3: Winget (Windows Package Manager)

```powershell
# Run PowerShell as Administrator
winget install Oracle.MySQL

# Start MySQL service
net start MySQL
```

## Post-Installation Verification

```powershell
# Check MySQL version
mysql --version

# Login to MySQL (use password you set during installation)
mysql -u root -p
```

## Default Credentials
- **Host**: localhost
- **Port**: 3306
- **Username**: root
- **Password**: (what you set during installation)

## Update .env File
After installation, update your `.env` file:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=municipal_chatbot
```
