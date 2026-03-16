@echo off
cls
echo ========================================
echo   FundEval Beta - Multi-Window Mode
echo ========================================
echo.

cd /d "%~dp0"

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
start "Frontend Server" cmd /k "set CONSOLE_NINJA_DISABLE=true && npx --yes vite@5.4.0"
cd ..

echo.
echo ========================================
echo   All services launched!
echo ========================================
echo.
echo Service URLs:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
pause
