#!/bin/bash
# 股票资讯系统 - Linux/Mac 启动脚本

echo "========================================"
echo "  股票资讯自动化系统"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[提示] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "[检查] 检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "[安装] 安装依赖..."
    pip install -r requirements.txt
fi

# 初始化数据库
if [ ! -d "data" ]; then
    mkdir -p data
fi

if [ ! -f "data/stock_news.db" ]; then
    echo "[初始化] 初始化数据库..."
    python -m config.database
fi

echo ""
echo "========================================"
echo "  请选择运行模式:"
echo "  1. 单次执行 (测试用)"
echo "  2. 启动定时任务"
echo "  3. 启动 Web 管理后台"
echo "  4. 退出"
echo "========================================"
echo ""

read -p "请输入选项 (1-4): " mode

case $mode in
    1)
        echo "[运行] 执行单次任务..."
        python main.py run
        ;;
    2)
        echo "[运行] 启动定时任务..."
        echo "按 Ctrl+C 停止"
        python main.py schedule
        ;;
    3)
        echo "[运行] 启动 Web 管理后台..."
        echo "访问 http://localhost:8000"
        python -m web.app
        ;;
    4)
        exit 0
        ;;
    *)
        echo "[错误] 无效选项"
        exit 1
        ;;
esac
