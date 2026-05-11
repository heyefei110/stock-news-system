@echo off
REM 股票资讯系统 - Windows 启动脚本

echo ========================================
echo   股票资讯自动化系统
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [提示] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo [检查] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [安装] 安装依赖...
    pip install -r requirements.txt
)

REM 初始化数据库
if not exist "data" (
    echo [提示] 创建数据目录...
    mkdir data
)

if not exist "data\stock_news.db" (
    echo [初始化] 初始化数据库...
    python -m config.database
)

echo.
echo ========================================
echo   请选择运行模式:
echo   1. 单次执行 (测试用)
echo   2. 启动定时任务
echo   3. 启动 Web 管理后台
echo   4. 退出
echo ========================================
echo.

set /p mode="请输入选项 (1-4): "

if "%mode%"=="1" (
    echo [运行] 执行单次任务...
    python main.py run
) else if "%mode%"=="2" (
    echo [运行] 启动定时任务...
    echo 按 Ctrl+C 停止
    python main.py schedule
) else if "%mode%"=="3" (
    echo [运行] 启动 Web 管理后台...
    echo 访问 http://localhost:8000
    python -m web.app
) else if "%mode%"=="4" (
    exit /b 0
) else (
    echo [错误] 无效选项
    exit /b 1
)

pause
