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

确保 `.env` 文件已配置：
- `GITHUB_TOKEN` - GitHub API Token
- `DEEPSEEK_API_KEY` - DeepSeek API Key
- `LLM_PROVIDER=deepseek` - LLM 提供商

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
- 检查 Python 版本（需要 3.8+）
- 确保所有依赖已安装
- 检查 `.env` 文件配置

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
