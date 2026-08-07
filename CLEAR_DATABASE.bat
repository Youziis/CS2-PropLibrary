@echo off
chcp 65001 >nul
echo ======================================================================
echo    清空数据库 - 重置所有数据
echo ======================================================================
echo.
echo ⚠️  警告：这将清空数据库中的所有道具数据！
echo.
echo 将会清空：
echo   1. SQLite 数据库中的所有道具记录
echo   2. public/data/ 中的所有导出数据
echo   3. public/images/ 中的所有导出图片
echo.
echo 不会删除：
echo   - 截图文件（output/screenshots/）
echo   - Demo 文件（demos/）
echo.
echo 按任意键继续，或关闭窗口取消...
pause >nul
echo.

echo 🗑️  正在清空数据库...
python -c "import sys; sys.path.insert(0, '.'); from backend.database import Database; db = Database(); db.cursor.execute('DELETE FROM utilities'); db.conn.commit(); print('✅ 数据库已清空')"

echo.
echo 🗑️  正在删除导出数据...

REM 删除数据文件
if exist public\data\*.json (
    del /Q public\data\*.json
    echo ✅ 已删除数据文件
) else (
    echo -- 数据目录为空
)

REM 删除图片文件（递归删除所有子目录）
if exist public\images\ (
    rmdir /S /Q public\images
    mkdir public\images
    echo ✅ 已删除所有图片
) else (
    echo -- 图片目录为空
)

echo.
echo ======================================================================
echo    清空完成！
echo ======================================================================
echo.
echo 📊 当前状态：
python -c "import sys; sys.path.insert(0, '.'); from backend.database import Database; db = Database(); count = len(db.get_utilities()); print(f'   数据库中道具数量: {count}')"
echo.
echo 💡 如果需要重新开始：
echo   1. 解析 Demo: python client\parse_demo.py
echo   2. 选择道具: 打开管理后台 http://localhost:5000
echo   3. 截图: python client\screenshot.py
echo.
pause
