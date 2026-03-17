@echo off
chcp 65001 >nul
echo ==========================================
echo FundEval Backend (Python 3.13)
echo ==========================================

set PROJECT_DIR=C:\Users\11639\Documents\trae_projects\0311-FundEval.Beta
set VENV_PATH=%PROJECT_DIR%\backend\.venv313\Scripts

REM Activate virtual environment
call "%VENV_PATH%\activate.bat"

REM Change to backend directory
cd /d "%PROJECT_DIR%\backend"

REM Start the backend server
echo Starting backend server...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload

pause
