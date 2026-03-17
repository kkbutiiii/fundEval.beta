@echo off
chcp 65001 >nul
cls
echo ========================================
echo   FundEval Beta - Windows Terminal
echo ========================================
echo.

cd /d "%~dp0"

:: Try to find Windows Terminal
set "WT_PATH="

:: Check common paths
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" (
    set "WT_PATH=%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"
) else if exist "%ProgramFiles%\WindowsApps\Microsoft.WindowsTerminal_*\wt.exe" (
    for /f "delims=" %%a in ('dir /b "%ProgramFiles%\WindowsApps\Microsoft.WindowsTerminal_*" 2^>nul') do (
        set "WT_PATH=%ProgramFiles%\WindowsApps\%%a\wt.exe"
    )
)

if not defined WT_PATH (
    echo ERROR: Windows Terminal not found!
    echo.
    echo Please install Windows Terminal from Microsoft Store
    echo or use start_backend_py313.bat to start backend only.
    echo.
    pause
    exit /b 1
)

echo Found Windows Terminal: %WT_PATH%
echo Starting services in tabs...
echo.

:: Set paths
set "PROJECT_DIR=%~dp0"
set "VENV_PATH=%PROJECT_DIR%backend\.venv313\Scripts"

:: Start Estimation Service tab
echo [1/3] Starting Estimation Service...
"%WT_PATH%" -w 0 nt --title "Estimation Service" -d "%PROJECT_DIR%estimation_service" cmd /k python run_all.py

timeout /t 1 /nobreak >nul

:: Start Backend tab with Python 3.13 virtual environment
echo [2/3] Starting Backend Server (Python 3.13)...
"%WT_PATH%" -w 0 nt --title "Backend Server (Py3.13)" -d "%PROJECT_DIR%backend" cmd /k "call .venv313\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload"

timeout /t 1 /nobreak >nul

:: Start Frontend tab
echo [3/3] Starting Frontend Server...
"%WT_PATH%" -w 0 nt --title "Frontend Server" -d "%PROJECT_DIR%frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Service URLs:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
echo Use Ctrl+Tab to switch between tabs
echo.
pause
