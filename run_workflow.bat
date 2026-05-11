@echo off
REM 触发 GitHub Actions 工作流

echo ========================================
echo   触发 GitHub Actions 工作流
echo ========================================
echo.
echo 正在打开 Actions 页面...
echo.
echo 请按以下步骤操作:
echo.
echo 1. 在打开的页面中，点击 "Run workflow" 按钮
echo 2. 点击绿色的 "Run workflow" 确认
echo 3. 等待 3-5 分钟
echo 4. 检查微信是否收到推送
echo.
echo 如果页面没有自动打开，请访问:
echo https://github.com/heyefei110/stock-news-system/actions/new
echo.
pause > nul

start https://github.com/heyefei110/stock-news-system/actions/new

echo.
echo 已打开页面，请点击运行工作流！
pause
