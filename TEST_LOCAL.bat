@echo off
chcp 65001 > nul
cls

echo.
echo ================================
echo   本地道具库测试服务器
echo ================================
echo.
echo 启动本地HTTP服务器...
echo 访问地址: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0public"
python -m http.server 8000
