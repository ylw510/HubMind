# PostgreSQL 快速安装指南

本文档提供 PostgreSQL 的一键安装和配置脚本，适用于 Ubuntu/Debian 系统。

## 🚀 一键安装脚本

```bash
#!/bin/bash
# PostgreSQL 快速安装和配置脚本

set -e

echo "📦 开始安装 PostgreSQL..."

# 1. 安装 PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 2. 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. 创建数据库和用户
echo "🔧 创建数据库和用户..."
sudo -u postgres psql -c "CREATE DATABASE hubmind;" 2>/dev/null || echo "数据库已存在"
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';" 2>/dev/null || echo "用户已存在"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;" 2>/dev/null || true

# 4. 配置访问权限
echo "🔐 配置访问权限..."
PG_VERSION=$(sudo -u postgres psql -tAc "SELECT version();" | grep -oP '\d+' | head -1)
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

# 检查是否已配置
if ! sudo grep -q "192.168.0.0/16" "$PG_HBA"; then
    sudo bash -c "echo 'host    all             all             192.168.0.0/16          scram-sha-256' >> $PG_HBA"
    echo "✅ 已添加网络访问权限"
else
    echo "ℹ️  网络访问权限已配置"
fi

# 5. 重新加载配置
sudo systemctl reload postgresql

# 6. 验证安装
echo "✅ 验证安装..."
sudo systemctl status postgresql --no-pager | head -3

echo ""
echo "🎉 PostgreSQL 安装完成！"
echo ""
echo "📋 配置信息："
echo "  数据库名: hubmind"
echo "  用户名: hubmind_user"
echo "  密码: hubmind_pass"
echo "  连接字符串: postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind"
echo ""
echo "📝 下一步："
echo "  在 backend/.env 中添加："
echo "  DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind"
```

## 📝 使用方法

### 方法 1: 直接运行脚本

```bash
# 保存脚本为 install_postgresql.sh
chmod +x install_postgresql.sh
./install_postgresql.sh
```

### 方法 2: 手动执行命令

```bash
# 1. 安装
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 2. 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE hubmind;"
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;"

# 3. 配置访问权限（如果需要）
PG_VERSION=$(sudo -u postgres psql -tAc "SELECT version();" | grep -oP '\d+' | head -1)
sudo bash -c "echo 'host    all             all             192.168.0.0/16          scram-sha-256' >> /etc/postgresql/$PG_VERSION/main/pg_hba.conf"
sudo systemctl reload postgresql

# 4. 配置 backend/.env
echo "DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind" >> backend/.env
```

## ✅ 验证安装

```bash
# 测试连接
psql -U hubmind_user -d hubmind -h localhost
# 输入密码: hubmind_pass
# 如果成功连接，输入 \q 退出

# 或使用 Python 测试
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✅ 数据库连接成功！')
        print(f'版本: {result.fetchone()[0][:50]}...')
except Exception as e:
    print(f'❌ 连接失败: {e}')
    sys.exit(1)
EOF
```

## 🔧 常见问题

### 问题 1: 数据库已存在

如果数据库或用户已存在，脚本会跳过创建步骤，这是正常的。

### 问题 2: 连接被拒绝

检查 PostgreSQL 服务是否运行：

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql  # 如果未运行
```

### 问题 3: 权限错误

确保已配置 `pg_hba.conf` 并重新加载：

```bash
sudo systemctl reload postgresql
```

## 📚 更多信息

- 详细配置说明请查看 [POSTGRESQL.md](POSTGRESQL.md)
- 如果遇到问题，请查看 [POSTGRESQL.md](POSTGRESQL.md) 的"常见问题"部分
