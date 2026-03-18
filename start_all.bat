@echo off
chcp 65001 >nul
cls
echo ========================================
echo   FundEval Beta - 启动脚本
echo ========================================
echo.

cd /d "%~dp0"

:: 设置项目目录
set "PROJECT_DIR=%~dp0"

echo 启动服务...
echo.

:: 启动 Estimation Service
echo [1/3] 启动 Estimation Service (端口 50802)...
start "Estimation Service" cmd /k "cd /d %PROJECT_DIR%estimation_service && python run_all.py"

timeout /t 2 /nobreak >nul

:: 启动 Backend
echo [2/3] 启动 Backend (端口 50801)...
start "Backend Server" cmd /k "cd /d %PROJECT_DIR%backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload"

timeout /t 2 /nobreak >nul

:: 启动 Frontend
echo [3/3] 启动 Frontend (端口 50888)...
start "Frontend Server" cmd /k "cd /d %PROJECT_DIR%frontend && npm run dev"

echo.
echo ========================================
echo 所有服务已启动！
echo ========================================
echo.
echo 访问地址:
echo   Estimation: http://localhost:50802
echo   Backend:    http://localhost:50801
echo   Frontend:   http://localhost:50888
echo.
echo 关闭本窗口不会停止服务
echo 请手动关闭各个服务窗口来停止
echo.
pause
