# HubMind Web 版使用指南

## 🎨 Web 界面

HubMind 现在提供了美观的 Web 界面，前端使用 React，后端使用 FastAPI。

## 📁 项目结构

```
HubMind/
├── backend/              # FastAPI 后端
│   ├── main.py          # API 主文件
│   └── requirements.txt  # 后端依赖
├── frontend/            # React 前端
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API 服务
│   │   └── App.jsx     # 主应用
│   └── package.json    # 前端依赖
└── start.sh            # 一键启动脚本
```

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

```bash
./start.sh
```

脚本会自动：
1. 检查并安装后端依赖
2. 检查并安装前端依赖
3. 启动后端服务（端口 8000）
4. 启动前端服务（端口 3000）

### 方法 2: 手动启动

#### 1. 启动后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r ../requirements.txt  # 安装主项目依赖
python main.py
```

后端将在 `http://localhost:8000` 运行

#### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:3000` 运行

## 🌐 访问应用

打开浏览器访问：**http://localhost:3000**

## 📱 功能页面

### 1. 💬 智能对话
- 与 HubMind 自然语言对话
- 支持 Markdown 渲染
- 代码高亮显示

### 2. 🔥 热门项目
- 按语言筛选
- 按时间范围筛选（今日/本周/本月）
- 显示 Stars、Forks、语言等信息

### 3. 📝 PR 分析
- 查看仓库的 Pull Requests
- 价值评分排序
- 显示 PR 状态、评论数等

### 4. 📋 Issue 管理
- 自然语言创建 Issue
- 自动分类和标签
- 相似 Issue 检测

### 5. 💚 仓库健康度
- PR 合并率
- 活跃贡献者
- 提交频率
- Issue 响应时间

### 6. ❓ 智能问答
- 询问仓库相关问题
- 基于 README、commits 等上下文回答

## 🔧 API 端点

后端提供以下 RESTful API：

- `POST /api/chat` - 对话接口
- `POST /api/trending` - 获取热门项目
- `POST /api/prs` - 获取 PR 列表
- `POST /api/analyze-pr` - 分析 PR
- `POST /api/create-issue` - 创建 Issue
- `POST /api/qa` - 问答接口
- `POST /api/health-repo` - 仓库健康度

详细 API 文档：访问 `http://localhost:8000/docs` (Swagger UI)

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代 Python Web 框架
- **Uvicorn** - ASGI 服务器
- **Pydantic** - 数据验证

### 前端
- **React 18** - UI 框架
- **Vite** - 构建工具
- **React Router** - 路由
- **TanStack Query** - 数据获取
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库
- **React Markdown** - Markdown 渲染

## 🎨 界面特点

- 🌙 深色主题（GitHub 风格）
- 📱 响应式设计
- ⚡ 快速加载
- 🎯 直观的导航
- 💫 流畅的交互

## 🔒 环境变量

### 必需配置

确保 `backend/.env` 文件已配置：

```env
# GitHub API
GITHUB_TOKEN=your_github_token_here

# LLM Provider
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# PostgreSQL Database（必需）
DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind
```

### PostgreSQL 配置

**Web 版需要 PostgreSQL 数据库**，用于存储用户账号和设置。

#### 快速安装 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE hubmind;"
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;"
```

#### 配置访问权限

如果遇到连接错误，需要配置 PostgreSQL 访问权限：

```bash
# 编辑配置文件
sudo nano /etc/postgresql/14/main/pg_hba.conf

# 添加以下行（在 # IPv4 local connections: 部分）
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             192.168.0.0/16          scram-sha-256

# 重新加载配置
sudo systemctl reload postgresql
```

详细说明请查看 [docs/POSTGRESQL.md](../docs/POSTGRESQL.md)

## 📝 开发说明

### 后端开发

```bash
cd backend
source venv/bin/activate
# 修改代码后，服务会自动重载
```

### 前端开发

```bash
cd frontend
npm run dev
# 修改代码后，页面会自动刷新
```

### 构建生产版本

```bash
cd frontend
npm run build
# 构建文件在 dist/ 目录
```

## 🐛 故障排除

### 后端无法启动

- **检查 Python 版本**（需要 3.8+）
- **确保所有依赖已安装**：`pip install -r backend/requirements.txt`
- **检查 `.env` 文件配置**：确保 `backend/.env` 存在且配置正确
- **检查 PostgreSQL**：
  - 确保 PostgreSQL 服务运行：`sudo systemctl status postgresql`
  - 确保数据库已创建：`sudo -u postgres psql -c "\l" | grep hubmind`
  - 检查 `DATABASE_URL` 配置是否正确
  - 查看详细错误信息：检查后端日志 `backend.log`

### 前端无法启动
- 检查 Node.js 版本（需要 16+）
- 删除 `node_modules` 重新安装：`rm -rf node_modules && npm install`
- 检查端口 3000 是否被占用

### API 调用失败
- 检查后端是否运行在 8000 端口
- 检查 CORS 配置
- 查看浏览器控制台错误信息

## 🎉 开始使用

1. 运行 `./start.sh` 或手动启动前后端
2. 访问 http://localhost:3000
3. 开始探索 GitHub！
