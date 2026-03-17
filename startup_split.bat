@echo off
cls
echo ========================================
echo   FundEval Beta - Split Pane Mode (3 Services)
echo ========================================
echo.

cd /d "%~dp0"

:: Try to find Windows Terminal
set "WT_PATH="

if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" (
    set "WT_PATH=%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"
) else if exist "%ProgramFiles%\WindowsApps\Microsoft.WindowsTerminal_*\wt.exe" (
    for /f "delims=" %%a in ('dir /b "%ProgramFiles%\WindowsApps\Microsoft.WindowsTerminal_*" 2^>nul') do (
        set "WT_PATH=%ProgramFiles%\WindowsApps\%%a\wt.exe"
    )
)

if not defined WT_PATH (
    echo ERROR: Windows Terminal not found!
    echo Please install Windows Terminal from Microsoft Store
    echo or use startup_multiwindow.bat instead.
    pause
    exit /b 1
)

echo Found Windows Terminal: %WT_PATH%
echo Starting services in split panes...
echo.

:: Layout: [Estimation][Frontend]
::         [Backend  ][empty]
:: Step 1: Start Estimation Service
:: Step 2: Split horizontally, start Backend (left column: Estimation top, Backend bottom)
:: Step 3: Move to Estimation, split vertically, start Frontend (top-right)
"%WT_PATH%" -w 0 nt --title "Estimation Service" -d "%~dp0estimation_service" cmd /k "python run_all.py" ; sp -H --title "Backend Server" -d "%~dp0backend" cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload" ; mf up ; sp -V --title "Frontend Server" -d "%~dp0frontend" cmd /k "npm run dev"

echo.
echo Services started in Windows Terminal split panes.
echo.
echo Service URLs:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
echo Layout: [Estimation][Frontend]
echo         [Backend  ][empty]
echo.
echo Use Alt+Arrow keys to navigate between panes
echo.
pause
