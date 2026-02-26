#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 启动 HubMind Web 应用"
echo ""

# 检查并停止已运行的服务
echo "🔍 检查端口占用..."
if command -v lsof >/dev/null 2>&1; then
  if lsof -ti:8000 >/dev/null 2>&1; then
    echo "⚠️  端口 8000 被占用，停止旧的后端服务..."
    pkill -f "python.*main.py" 2>/dev/null || true
    sleep 2
  fi
  if lsof -ti:3000 >/dev/null 2>&1; then
    echo "⚠️  端口 3000 被占用，停止旧的前端服务..."
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true
    sleep 2
  fi
else
  echo "⚠️  未安装 lsof，跳过端口检查"
fi
echo ""

# 检查后端依赖
PYVENV="backend/venv/bin/python3"
if [ ! -d "backend/venv" ]; then
  echo "📦 创建后端虚拟环境..."
  python3 -m venv backend/venv
  $PYVENV -m ensurepip --upgrade 2>/dev/null || true
  echo "📦 安装后端依赖..."
  $PYVENV -m pip install -q -r backend/requirements.txt -r requirements.txt
  echo "✅ 后端依赖已安装"
elif ! $PYVENV -c "import fastapi" 2>/dev/null; then
  echo "📦 后端 venv 缺少依赖，正在安装..."
  $PYVENV -m pip install -q -r backend/requirements.txt -r requirements.txt
  echo "✅ 后端依赖已安装"
else
  echo "✅ 后端依赖已就绪"
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
  echo "📦 安装前端依赖..."
  cd frontend && npm install && cd ..
else
  echo "✅ 前端依赖已存在"
fi

echo ""
echo "启动服务..."
echo ""

# 启动后端（从项目根运行 backend/main.py，监听 0.0.0.0 以便局域网访问）
echo "🔧 启动后端 (0.0.0.0:8000)..."
if [ ! -x "backend/venv/bin/python3" ]; then
  echo "❌ 未找到 backend/venv/bin/python3，请先安装: sudo apt install python3.12-venv，然后重新运行本脚本"
  exit 1
fi
# 从 backend/.env 导出 DATABASE_URL，避免子进程未正确加载 .env 导致无密码连接
if [ -f "backend/.env" ]; then
  DATABASE_URL=$(grep '^DATABASE_URL=' backend/.env | cut -d= -f2- | tr -d '\r"')
  export DATABASE_URL
fi
$PYVENV backend/main.py &
BACKEND_PID=$!

# 等待后端就绪
echo "等待后端就绪..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null | grep -q 200; then
    echo "✅ 后端已就绪"
    break
  fi
  sleep 1
done
if ! curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null | grep -q 200; then
  echo "⚠️  后端可能未成功启动，请查看上方报错。继续启动前端..."
fi

# 启动前端
echo "🎨 启动前端 (端口 3000)..."
(
  cd frontend
  exec npm run dev
) &
FRONTEND_PID=$!

# 本机 IP（用于从其他设备访问时提示）
LOCAL_IP=""
if command -v hostname >/dev/null 2>&1; then
  if command -v ip >/dev/null 2>&1; then
    LOCAL_IP=$(ip route get 1 2>/dev/null | grep -oP 'src \K\S+' || true)
  fi
  [ -z "$LOCAL_IP" ] && LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

echo ""
echo "----------------------------------------"
echo "✅ 服务已启动"
echo ""
echo "  本机访问："
echo "    前端: http://localhost:3000"
echo "    后端: http://localhost:8000"
echo ""
if [ -n "$LOCAL_IP" ]; then
  echo "  从其他设备访问（同一局域网）时："
  echo "    前端: http://${LOCAL_IP}:3000"
  echo "    后端 API 地址（在登录页填写）: http://${LOCAL_IP}:8000"
  echo ""
fi
echo "  按 Ctrl+C 停止所有服务"
echo "----------------------------------------"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
