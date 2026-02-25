#!/bin/bash

# 快速安装后端依赖脚本（使用国内镜像源）

echo "📦 使用国内镜像源快速安装后端依赖..."
echo ""

cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip（使用清华镜像）
echo "升级 pip..."
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖（使用清华镜像，增加超时时间）
echo "安装后端依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout=120

echo "安装主项目依赖..."
pip install -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout=120

echo ""
echo "✅ 依赖安装完成！"
