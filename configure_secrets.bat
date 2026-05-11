@echo off
REM 配置 GitHub Secrets 脚本

echo ========================================
echo   配置 GitHub Secrets
echo ========================================
echo.
echo 由于 GitHub API 需要认证，请手动配置 Secrets
echo.
echo 步骤 1: 打开浏览器访问
echo https://github.com/heyefei110/stock-news-system/settings/secrets/actions
echo.
echo 步骤 2: 点击 "New repository secret"
echo.
echo 步骤 3: 添加以下两个密钥
echo.
echo   Name: DASHSCOPE_API_KEY
echo   Value: sk-676b1e0e231740f78344673190948d4d
echo.
echo   Name: SERVERCHAN_SENDKEY
echo   Value: SCT348288TAnib06tVISfWrgSkobqb3jRa
echo.
echo ========================================
echo.
echo 按任意键打开 GitHub 页面...
pause > nul

REM 尝试打开浏览器
start https://github.com/heyefei110/stock-news-system/settings/secrets/actions

echo.
echo 配置完成后，访问以下地址测试运行:
echo https://github.com/heyefei110/stock-news-system/actions
echo.
pause
