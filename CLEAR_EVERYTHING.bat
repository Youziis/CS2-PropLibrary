@echo off
echo ======================================================================
echo    清空线上发布的数据，保留本地截图和待审核
echo ======================================================================
echo.
echo 这将清空：
echo   1. 已批准道具列表
echo   2. public/data/ 中的所有数据文件
echo   3. public/images/ 中的所有图片
echo.
echo 不会删除：
echo   - 待审核道具（可以重新审核）
echo   - 截图文件（output/screenshots/）
echo.
pause
echo.

REM 清空已批准列表
echo 正在清空已批准列表...
echo [] > output\data\approved.json
echo OK 已批准列表已清空

echo.
echo 正在删除前台数据...

REM 删除数据文件
if exist public\data\*.json (
    del /Q public\data\*.json
    echo OK 已删除数据文件
) else (
    echo -- 数据目录为空
)

REM 删除图片文件
if exist public\images\*.jpg (
    del /Q public\images\*.jpg
    echo OK 已删除 JPG 图片
) else (
    echo -- 无 JPG 图片
)

if exist public\images\*.png (
    del /Q public\images\*.png
    echo OK 已删除 PNG 图片
) else (
    echo -- 无 PNG 图片
)

echo.
echo ======================================================================
echo    清空完成！
echo ======================================================================
echo.
echo 下一步操作：
echo.
echo 1. 打开 GitHub Desktop
echo 2. 提交信息：清空所有道具
echo 3. 点击 Commit to main
echo 4. 点击 Push origin
echo.
echo 或使用命令行：
echo    git add output/data/approved.json public/
echo    git commit -m "清空所有道具"
echo    git push
echo.
echo 5. 等待 1-2 分钟 Cloudflare 自动部署
echo 6. 访问网站验证：https://yuuko-cs2.bb1623490499.workers.dev
echo.
pause
