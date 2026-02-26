# HubMind 使用 PostgreSQL 说明

HubMind 后端使用 **PostgreSQL** 存储用户账号与设置，本文说明如何安装、配置与维护。

---

## 1. 概述

- **数据库名**：`hubmind`（可自定，需与连接串一致）
- **用途**：用户注册/登录（`users`）、用户设置如 GitHub Token / LLM 配置（`user_settings`）
- **连接配置**：通过 `backend/.env` 中的 `DATABASE_URL` 或 `POSTGRES_URL` 指定

---

## 2. 安装 PostgreSQL

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 其他系统

请参考 [PostgreSQL 官方文档](https://www.postgresql.org/download/)。

---

## 3. 创建数据库与用户

以 `postgres` 系统用户进入 psql：

```bash
sudo -u postgres psql
```

在 psql 中执行：

```sql
-- 创建数据库
CREATE DATABASE hubmind;

-- 创建角色（用户），并允许登录
CREATE ROLE hubmind WITH LOGIN PASSWORD '你的密码';

-- 授权：hubmind 对 hubmind 库拥有全部权限
GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind;

-- 若使用 PostgreSQL 15+，还需授予 schema 权限
\c hubmind
GRANT ALL ON SCHEMA public TO hubmind;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hubmind;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hubmind;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hubmind;
```

若角色已存在、只需设密码：

```sql
ALTER ROLE hubmind WITH PASSWORD '你的密码';
```

---

## 4. 配置连接串

在项目根目录下：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，设置 `DATABASE_URL`：

```env
# 格式: postgresql://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql://hubmind:你的密码@localhost:5432/hubmind
```

注意：

- 密码中若含特殊字符（如 `@`、`#`、`:`），需做 [URL 编码](https://en.wikipedia.org/wiki/Percent-encoding)。
- 也可使用环境变量 `POSTGRES_URL`，与 `DATABASE_URL` 二选一即可；优先使用 `backend/.env` 文件中的配置。

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

## 7. 常见问题

### 7.1 报错：`fe_sendauth: no password supplied`

- **原因**：连接串中未带密码，或 `.env` 未生效。
- **处理**：
  1. 确认 `backend/.env` 中为 `DATABASE_URL=postgresql://hubmind:密码@localhost:5432/hubmind`（中间有 `:密码`）。
  2. 确认磁盘上的 `.env` 已保存（有时编辑器与磁盘不一致）。
  3. 若用 `./start.sh` 启动，脚本会从 `backend/.env` 导出 `DATABASE_URL`；仍失败时，后端会尝试从 `backend/.env` 文件直接读取。

### 7.2 如何查看当前有哪些用户？

```bash
sudo -u postgres psql -d hubmind -c "SELECT id, username, created_at FROM users;"
```

### 7.3 如何查看 PostgreSQL 中的角色（用户）？

```bash
sudo -u postgres psql -c "\du"
```

---

## 8. 备份与恢复

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

## 9. 相关文件

| 文件/目录           | 说明                    |
|---------------------|-------------------------|
| `backend/.env`      | 本地配置，含 `DATABASE_URL`（勿提交） |
| `backend/.env.example` | 配置示例               |
| `backend/database.py`  | 连接配置、模型与 `init_db()` |
