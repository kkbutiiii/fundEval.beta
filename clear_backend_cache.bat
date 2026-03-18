@echo off
chcp 65001 >nul
echo ==========================================
echo       清除后端缓存
echo ==========================================
echo.

:: 删除基金列表本地文件缓存
echo [1/2] 删除基金列表本地文件缓存...
if exist "backend\cache\fund_list_cache.json" (
    del /f "backend\cache\fund_list_cache.json"
    echo       - 已删除 fund_list_cache.json
) else (
    echo       - fund_list_cache.json 不存在
)

if exist "backend\cache\fund_list_metadata.json" (
    del /f "backend\cache\fund_list_metadata.json"
    echo       - 已删除 fund_list_metadata.json
) else (
    echo       - fund_list_metadata.json 不存在
)

echo.
echo [2/2] 缓存清除完成！
echo.
echo ==========================================
echo 注意：内存缓存(TTLCache、日内估值缓存)
echo       需要重启后端服务才能完全清除。
echo ==========================================
echo.
pause
