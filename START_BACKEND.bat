@echo off
chcp 65001 >nul
echo ========================================
echo 启动管理后台（新版 - 基于数据库）
echo ========================================
echo.

echo 📦 检查依赖...
echo.
echo 尝试方案1：临时禁用代理安装...
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
python -m pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  方案1失败，尝试方案2：使用官方源...
    python -m pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend\requirements.txt
)

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  方案2失败，尝试方案3：使用代理...
    set HTTP_PROXY=http://127.0.0.1:10809
    set HTTPS_PROXY=http://127.0.0.1:10809
    python -m pip install --no-cache-dir -r backend\requirements.txt
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖安装失败！请手动安装：
    echo    pip install flask==3.0.0 flask-cors==4.0.0
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 依赖检查完成
echo.
echo 🚀 启动服务器...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
python backend\app.py
pause
