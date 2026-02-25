#!/bin/bash

echo "🚀 启动 HubMind Web 应用"
echo ""

# 检查并停止已运行的服务
echo "🔍 检查端口占用..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  端口 8000 被占用，停止旧的后端服务..."
    pkill -f "python.*main.py" 2>/dev/null
    sleep 2
fi

if lsof -ti:3000 > /dev/null 2>&1; then
    echo "⚠️  端口 3000 被占用，停止旧的前端服务..."
    pkill -f "vite" 2>/dev/null
    sleep 2
fi

echo ""

# 检查后端依赖
if [ ! -d "backend/venv" ]; then
    echo "📦 安装后端依赖..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    # 使用清华镜像源加速安装
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout=60
    pip install -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout=60
    cd ..
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ 依赖已安装"
echo ""
echo "启动服务..."
echo ""

# 启动后端
echo "🔧 启动后端服务 (端口 8000)..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务 (端口 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 服务已启动！"
echo ""
echo "📱 前端: http://localhost:3000"
echo "🔧 后端: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
