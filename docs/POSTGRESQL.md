# HubMind 使用 PostgreSQL 说明

HubMind 后端使用 **PostgreSQL** 存储用户账号与设置，本文说明如何安装、配置与维护。

> 💡 **快速安装**：如果你使用 Ubuntu/Debian 系统，可以使用 [快速安装脚本](POSTGRESQL_QUICK_SETUP.md) 一键完成安装和配置。

---

## 1. 概述

- **数据库名**：`hubmind`（可自定，需与连接串一致）
- **用途**：用户注册/登录（`users`）、用户设置如 GitHub Token / LLM 配置（`user_settings`）
- **连接配置**：通过 `backend/.env` 中的 `DATABASE_URL` 或 `POSTGRES_URL` 指定

---

## 2. 安装 PostgreSQL

### Ubuntu / Debian

```bash
# 更新包列表
sudo apt update

# 安装 PostgreSQL 和扩展
sudo apt install postgresql postgresql-contrib

# 启动 PostgreSQL 服务
sudo systemctl start postgresql

# 设置开机自启
sudo systemctl enable postgresql

# 验证安装
sudo systemctl status postgresql
```

### macOS

使用 Homebrew：

```bash
brew install postgresql@14
brew services start postgresql@14
```

### Windows

1. 从 [PostgreSQL 官网](https://www.postgresql.org/download/windows/) 下载安装程序
2. 运行安装程序，按提示完成安装
3. 记住安装时设置的 postgres 用户密码

### 其他系统

请参考 [PostgreSQL 官方文档](https://www.postgresql.org/download/)。

---

## 3. 创建数据库与用户

### 方法 1: 使用命令行（推荐）

```bash
# 创建数据库
sudo -u postgres psql -c "CREATE DATABASE hubmind;"

# 创建用户（推荐使用 hubmind_user 作为用户名）
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';"

# 授权数据库权限
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"

# 授权 schema 权限（PostgreSQL 14+）
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;"
```

### 方法 2: 使用 psql 交互式命令行

以 `postgres` 系统用户进入 psql：

```bash
sudo -u postgres psql
```

在 psql 中执行：

```sql
-- 创建数据库
CREATE DATABASE hubmind;

-- 创建角色（用户），并允许登录
CREATE USER hubmind_user WITH LOGIN PASSWORD 'hubmind_pass';

-- 授权：hubmind_user 对 hubmind 库拥有全部权限
GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;

-- 切换到 hubmind 数据库
\c hubmind

-- 授予 schema 权限（PostgreSQL 14+）
GRANT ALL ON SCHEMA public TO hubmind_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hubmind_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hubmind_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hubmind_user;
```

### 验证创建

```bash
# 查看数据库列表
sudo -u postgres psql -c "\l" | grep hubmind

# 查看用户列表
sudo -u postgres psql -c "\du" | grep hubmind_user

# 测试连接
psql -U hubmind_user -d hubmind -h localhost
# 输入密码: hubmind_pass
```

**注意**：如果角色已存在，只需修改密码：

```sql
ALTER USER hubmind_user WITH PASSWORD '新密码';
```

---

## 4. 配置连接串

### 4.1 创建 backend/.env 文件

如果 `backend/.env` 不存在，创建它：

```bash
cd /path/to/HubMind/backend
touch .env
```

### 4.2 添加数据库配置

编辑 `backend/.env`，添加 `DATABASE_URL`：

```env
# PostgreSQL 数据库配置
# 格式: postgresql://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind
```

**完整示例**（包含其他配置）：

```env
# GitHub API Configuration
GITHUB_TOKEN=your_github_token_here

# LLM Provider Configuration
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind
```

### 4.3 注意事项

- **密码特殊字符**：如果密码中包含特殊字符（如 `@`、`#`、`:`、`%`），需要进行 [URL 编码](https://en.wikipedia.org/wiki/Percent-encoding)
  - `@` → `%40`
  - `#` → `%23`
  - `:` → `%3A`
  - `%` → `%25`

  例如：密码 `p@ss#word` 应写为 `p%40ss%23word`

- **环境变量优先级**：
  - 优先使用 `backend/.env` 文件中的 `DATABASE_URL`
  - 其次使用环境变量 `POSTGRES_URL`
  - 最后使用环境变量 `DATABASE_URL`

- **远程连接**：如果需要连接远程 PostgreSQL 服务器，将 `localhost` 替换为服务器 IP 或域名

---

## 5. 表结构

应用首次启动时会自动执行 `init_db()`，创建以下表（定义见 `backend/database.py`）。

### 5.1 `users`（用户账号）

| 列名          | 类型        | 说明           |
|---------------|-------------|----------------|
| `id`          | Integer     | 主键           |
| `username`    | String(64)  | 用户名，唯一   |
| `password_hash` | String(256) | 密码 bcrypt 哈希 |
| `created_at`  | DateTime    | 注册时间       |

### 5.2 `user_settings`（用户设置）

| 列名          | 类型    | 说明                    |
|---------------|---------|-------------------------|
| `id`          | Integer | 主键                    |
| `user_id`     | Integer | 外键 → `users.id`，一对一 |
| `github_token`| Text    | GitHub Token            |
| `llm_provider`| String(32) | LLM 提供商，默认 deepseek |
| `llm_api_key` | Text    | LLM API Key             |
| `llm_base_url`| Text    | 自定义 LLM API 地址（openai_compatible） |
| `llm_model`   | String(128) | 自定义模型名（openai_compatible） |
| `updated_at`  | DateTime | 最后更新时间           |

若 `user_settings` 表已存在，需手动加列：
`ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS llm_base_url TEXT DEFAULT '';`
`ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS llm_model VARCHAR(128) DEFAULT '';`

---

## 6. 启动与连接池

- 启动方式：在项目根执行 `./start.sh`，或单独启动后端（会从 `backend/.env` 读 `DATABASE_URL`）。
- 后端使用 SQLAlchemy 连接池：`pool_size=10`，`max_overflow=20`，`pool_pre_ping=True`，`pool_recycle=300`（秒）。

---

## 7. 配置访问权限（重要）

如果遇到连接错误 `no pg_hba.conf entry for host`，需要配置 PostgreSQL 的访问权限。

### 7.1 找到配置文件

```bash
# Ubuntu/Debian
sudo find /etc/postgresql -name "pg_hba.conf"

# 通常路径：/etc/postgresql/14/main/pg_hba.conf（14 是版本号）
```

### 7.2 编辑 pg_hba.conf

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

在 `# IPv4 local connections:` 部分添加：

```
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             192.168.0.0/16          scram-sha-256
```

### 7.3 重新加载配置

```bash
sudo systemctl reload postgresql
```

### 7.4 验证连接

```bash
# 测试连接
psql -U hubmind_user -d hubmind -h localhost
# 输入密码后应能成功连接
```

## 8. 常见问题

### 8.1 报错：`fe_sendauth: no password supplied`

- **原因**：连接串中未带密码，或 `.env` 未生效。
- **处理**：
  1. 确认 `backend/.env` 中为 `DATABASE_URL=postgresql://hubmind_user:密码@localhost:5432/hubmind`（中间有 `:密码`）。
  2. 确认磁盘上的 `.env` 已保存（有时编辑器与磁盘不一致）。
  3. 若用 `./start.sh` 启动，脚本会从 `backend/.env` 导出 `DATABASE_URL`；仍失败时，后端会尝试从 `backend/.env` 文件直接读取。

### 8.2 报错：`no pg_hba.conf entry for host`

- **原因**：PostgreSQL 未配置允许该 IP 地址连接。
- **处理**：参考 [7. 配置访问权限](#7-配置访问权限重要) 章节。

### 8.3 报错：`connection to server at "localhost" failed`

- **原因**：PostgreSQL 服务未启动。
- **处理**：
  ```bash
  sudo systemctl start postgresql
  sudo systemctl status postgresql
  ```

### 8.4 如何查看当前有哪些用户？

```bash
sudo -u postgres psql -d hubmind -c "SELECT id, username, created_at FROM users;"
```

### 8.5 如何查看 PostgreSQL 中的角色（用户）？

```bash
sudo -u postgres psql -c "\du"
```

### 8.6 如何查看数据库列表？

```bash
sudo -u postgres psql -c "\l"
```

### 8.7 如何重置数据库？

```bash
# 删除数据库（谨慎操作！）
sudo -u postgres psql -c "DROP DATABASE IF EXISTS hubmind;"

# 重新创建
sudo -u postgres psql -c "CREATE DATABASE hubmind;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;"

# 重启后端服务，会自动创建表
```

---

## 9. 验证安装

在配置完成后，验证数据库连接和表创建：

```bash
cd /path/to/HubMind

# 测试数据库连接
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.fetchone()[0]
        print('✅ 数据库连接成功！')
        print(f'PostgreSQL 版本: {version[:60]}...')
except Exception as e:
    print(f'❌ 连接失败: {e}')
    sys.exit(1)
EOF

# 初始化数据库表
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from database import init_db

try:
    init_db()
    print('✅ 数据库表初始化成功！')
except Exception as e:
    print(f'❌ 初始化失败: {e}')
    sys.exit(1)
EOF
```

## 10. 备份与恢复

### 备份

```bash
sudo -u postgres pg_dump -Fc hubmind > hubmind_$(date +%Y%m%d).dump
```

### 恢复

```bash
sudo -u postgres pg_restore -d hubmind -c hubmind_YYYYMMDD.dump
```

（`-c` 会先删除已存在对象，慎用；可先建空库再恢复。）

---

## 11. 相关文件

| 文件/目录           | 说明                    |
|---------------------|-------------------------|
| `backend/.env`      | 本地配置，含 `DATABASE_URL`（勿提交） |
| `backend/.env.example` | 配置示例               |
| `backend/database.py`  | 连接配置、模型与 `init_db()` |
