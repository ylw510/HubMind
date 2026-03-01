# HubMind 快速开始指南

## 🚀 5 分钟快速设置

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

> 💡 **加速安装**：如果安装较慢，可以使用国内镜像源：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```
> 或配置永久镜像：创建 `~/.pip/pip.conf`，添加：
> ```ini
> [global]
> index-url = https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 步骤 2: 配置环境变量

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加你的凭证：

```env
# GitHub API Token（必需）
GITHUB_TOKEN=ghp_your_token_here

# LLM Provider（默认使用 DeepSeek）
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your_deepseek_key_here
```

**获取 API Keys：**
- **GitHub Token**: 访问 https://github.com/settings/tokens , 生成 token 并选择 `repo` 权限
- **DeepSeek API Key**: 访问 https://platform.deepseek.com/ , 注册并创建 API Key

> 📖 **其他 LLM 提供商**：查看 [LLM_SUPPORT.md](LLM_SUPPORT.md) 了解如何配置 OpenAI、Claude、Gemini 等

### 步骤 3: PostgreSQL 配置（仅 Web 版需要）

如果只使用 CLI 版本，可以跳过此步骤。

如果使用 Web 界面，需要安装 PostgreSQL：

```bash
# 快速安装（Ubuntu/Debian）
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE hubmind;"
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
sudo -u postgres psql -d hubmind -c "GRANT ALL ON SCHEMA public TO hubmind_user;"

# 配置 backend/.env
echo "DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind" >> backend/.env
```

> 📖 **详细说明**：查看 [docs/POSTGRESQL_QUICK_SETUP.md](docs/POSTGRESQL_QUICK_SETUP.md) 或 [docs/POSTGRESQL.md](docs/POSTGRESQL.md)

### 步骤 4: 验证安装

```bash
# 验证配置
python3 -c "from config import Config; Config.validate(); print('✅ 配置正确')"

# 测试获取热门项目
python main.py trending --limit 5

# 测试交互式模式
python main.py interactive
```

## 📋 Common Commands

### Get Trending Repositories
```bash
python main.py trending
python main.py trending --language python
python main.py trending --since weekly --limit 20
```

### Analyze Pull Requests
```bash
python main.py prs owner/repo
python main.py prs owner/repo --valuable
python main.py analyze-pr owner/repo 12345
```

### Create Issues
```bash
python main.py create-issue owner/repo "Your issue description here"
```

### Chat with HubMind
```bash
python main.py chat "Show me trending Python projects"
python main.py interactive
```

### Ask Questions
```bash
python main.py ask owner/repo "What language is this project?"
```

### Health Check
```bash
python main.py health owner/repo
```

## 🎯 First Steps

1. **Try trending repos:**
   ```bash
   python main.py trending --language python --limit 10
   ```

2. **Analyze a popular repo's PRs:**
   ```bash
   python main.py prs microsoft/vscode --valuable
   ```

3. **Start interactive mode:**
   ```bash
   python main.py interactive
   ```
   Then try:
   - "Show me today's top 5 trending JavaScript projects"
   - "What are the most valuable PRs in facebook/react today?"
   - "Create an issue in my-repo/awesome-project saying 'Add dark mode'"

## ⚠️ 故障排除

### 错误: GITHUB_TOKEN is required
- 确保已创建 `.env` 文件
- 检查 token 是否有 `repo` 权限
- 验证 token 格式是否正确

### 错误: DEEPSEEK_API_KEY is required
- 在 `.env` 文件中添加 DeepSeek API key
- 确保 API key 有效且有余额
- 查看 [docs/DEEPSEEK.md](docs/DEEPSEEK.md) 获取详细配置说明

### 错误: Rate limit exceeded
- GitHub API 有速率限制
- 等待几分钟后重试
- 考虑使用具有更高限制的 token

### 导入错误 (Import errors)
- 确保在项目根目录运行命令
- 重新安装依赖：`pip install -r requirements.txt`
- 检查 Python 版本（需要 3.8+）

### 数据库连接错误 (Web 版)
- 确保 PostgreSQL 已安装并运行：`sudo systemctl status postgresql`
- 检查 `backend/.env` 中的 `DATABASE_URL` 配置
- 确保数据库和用户已创建
- 查看 [docs/POSTGRESQL.md](docs/POSTGRESQL.md) 获取详细帮助

### pip 安装缓慢
- 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 配置永久镜像：创建 `~/.pip/pip.conf`，添加：
  ```ini
  [global]
  index-url = https://pypi.tuna.tsinghua.edu.cn/simple
  timeout = 120
  ```

## 💡 Tips

- Use `--help` with any command to see options
- Interactive mode remembers conversation context
- Value scores help identify important PRs
- Similar issue detection prevents duplicates

## 📚 下一步

- 阅读完整的 [README.md](README.md) 了解详细功能
- 查看 [WEB_README.md](WEB_README.md) 了解 Web 界面使用
- 查看 [LLM_SUPPORT.md](LLM_SUPPORT.md) 了解其他 LLM 提供商配置
- 运行 `python main.py --help` 查看所有可用命令
