#!/usr/bin/env python3
# 若终端只有 python3：使用 python3 run_backend.py 或 .venv/bin/python run_backend.py
"""
从项目根目录启动 HubMind 后端（避免 cd backend 后路径问题）。
在 HubMind 目录下执行: python run_backend.py
"""
import os
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    print("HubMind 后端启动中… (Ctrl+C 停止)")
    print("  本机访问: http://127.0.0.1:8000")
    print("  健康检查: http://127.0.0.1:8000/api/health")
    print("-" * 50)

    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )

if __name__ == "__main__":
    main()
