#!/usr/bin/env bash
# 在项目根目录执行: ./run_backend.sh  或  bash run_backend.sh
cd "$(dirname "$0")"
echo "HubMind 后端启动中… (Ctrl+C 停止)"
echo "  本机访问: http://127.0.0.1:8000"
echo "  若前端在别的机器，请用本机 IP: http://<本机IP>:8000"
echo "----------------------------------------"
exec python3 run_backend.py
