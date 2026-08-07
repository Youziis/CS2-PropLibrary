@echo off
chcp 65001 >nul
echo ======================================================================
echo    清空已导出数据 - 保留待审核道具
echo ======================================================================
echo.
echo 这将清空：
echo   1. 数据库中 exported 状态的道具（改回 approved 状态）
echo   2. public/data/ 中的所有导出数据
echo   3. public/images/ 中的所有导出图片
echo.
echo 保留：
echo   - 待审核道具（screenshotted）
echo   - 已批准道具（approved）
echo   - 截图文件（output/screenshots/）
echo.
echo 按任意键继续，或关闭窗口取消...
pause >nul
echo.

echo 🔄 正在重置已导出道具状态...
python -c "import sys; sys.path.insert(0, '.'); from backend.database import Database; db = Database(); exported = db.get_utilities(status='exported'); count = 0; [db.update_status(u['hash'], 'approved') for u in exported]; print(f'✅ 已重置 {len(exported)} 个道具状态')"

echo.
echo 🗑️  正在删除导出文件...

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
python -c "import sys; sys.path.insert(0, '.'); from backend.database import Database; db = Database(); stats = db.get_statistics(); print(f'   待审核: {stats.get(\"screenshotted\", 0)} 个'); print(f'   已批准: {stats.get(\"approved\", 0)} 个'); print(f'   已导出: {stats.get(\"exported\", 0)} 个')"
echo.
echo 💡 下一步：
echo   1. 重新审核道具（如果需要）
echo   2. 导出道具到用户端
echo   3. 推送到 GitHub 发布
echo.
pause
