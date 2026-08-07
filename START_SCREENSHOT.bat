@echo off
chcp 65001 >nul
echo ======================================================================
echo    CS2 道具自动截图
echo ======================================================================
echo.
echo ⚠️  准备工作：
echo   1. 确保后端服务器正在运行 (http://localhost:5000)
echo   2. 已在管理后台选择好要截图的道具
echo   3. 启动 CS2 游戏并进入对应地图
echo   4. 选择队伍（T 或 CT）
echo   5. 确保游戏窗口在前台
echo.
pause
echo.
echo 🚀 启动截图脚本...
echo    (脚本会自动处理数据导出和同步)
echo.
cd client
python screenshot.py
cd ..
echo.
pause
