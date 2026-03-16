@echo off
cls
echo ========================================
echo   FundEval Beta - Tab Mode (WT)
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
    echo or use startup_multiwindow.bat instead.
    echo.
    pause
    exit /b 1
)

echo Found Windows Terminal: %WT_PATH%
echo Starting services in tabs...
echo.

:: Start Estimation Service tab
echo [1/3] Starting Estimation Service...
"%WT_PATH%" -w 0 nt --title "Estimation Service" -d "%~dp0estimation_service" cmd /k python run_all.py

timeout /t 1 /nobreak >nul

:: Start Backend tab
echo [2/3] Starting Backend Server...
"%WT_PATH%" -w 0 nt --title "Backend Server" -d "%~dp0backend" cmd /k uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload

timeout /t 1 /nobreak >nul

:: Start Frontend tab - use cmd /k to ensure npm is available
echo [3/3] Starting Frontend Server...
"%WT_PATH%" -w 0 nt --title "Frontend Server" -d "%~dp0frontend" cmd /k "set CONSOLE_NINJA_DISABLE=true && npx --yes vite@5.4.0"

echo.
echo Services started in Windows Terminal tabs.
echo.
echo Service URLs:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
echo Use Ctrl+Tab to switch between tabs
echo.
pause
