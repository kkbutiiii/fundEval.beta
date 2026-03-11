@echo off
cls
echo ========================================
echo   FundEval Beta - Startup Script
echo ========================================
echo.

cd /d "%~dp0"

:: Check if Windows Terminal is available
where wt >nul 2>nul
if %errorlevel% == 0 (
    echo Starting services in Windows Terminal tabs...
    echo.
    wt -w 0 nt --title "Estimation Service" -d "%~dp0estimation_service" python run_all.py ; nt --title "Backend Server" -d "%~dp0backend" uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload ; nt --title "Frontend Server" -d "%~dp0frontend" npm run dev -- --port 50888
    echo.
    echo Services started in Windows Terminal tabs.
    echo Use Ctrl+Tab to switch between tabs
) else (
    echo Windows Terminal not found, starting in separate windows...
    echo.

    echo [1/3] Starting Estimation Service (Port 50802)...
    cd estimation_service
    start "Estimation Service" cmd /k python run_all.py
    cd ..
    timeout /t 2 /nobreak >nul

    echo [2/3] Starting Backend Server (Port 50801)...
    cd backend
    start "Backend Server" cmd /k uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload
    cd ..
    timeout /t 2 /nobreak >nul

    echo [3/3] Starting Frontend Server (Port 50888)...
    cd frontend
    start "Frontend Server" cmd /k npm run dev -- --port 50888
    cd ..

    echo.
    echo ========================================
    echo   All services launched!
    echo ========================================
)

echo.
echo Service URLs:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
pause
