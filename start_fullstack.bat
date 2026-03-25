@echo off
setlocal

echo Starting Municipal Chatbot full stack...

set "BACKEND_DIR=c:\Users\admin\OneDrive\Desktop\municipal chatbot"
set "FRONTEND_DIR=c:\Users\admin\OneDrive\Desktop\municipal-chatbot-nextjs"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python venv not found at: %PYTHON_EXE%
  exit /b 1
)

start "Municipal Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && "%PYTHON_EXE%" backend_api.py"
start "Municipal Frontend (Next.js)" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo Backend:  http://localhost:5000/health
echo Frontend: http://localhost:3000
echo.
echo Open both terminal windows and keep them running.

endlocal
