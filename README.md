# HubMind 🤖

**HubMind** - Your Intelligent GitHub Assistant powered by LangChain and GitHub API

HubMind is an intelligent agent that helps you discover trending repositories, analyze pull requests, manage issues, and interact with GitHub using natural language.

## ✨ Features

### 🎯 Core Features

1. **Trend Discovery** - Find trending GitHub repositories by language, time range
2. **PR Analysis** - Discover valuable pull requests and analyze them in detail
3. **Issue Management** - Create issues from natural language descriptions
4. **Smart Q&A** - Ask questions about repositories and get intelligent answers
5. **Health Monitoring** - Track repository health metrics and activity
6. **Automation** - Batch operations and workflow automation

### 🚀 Extended Features

- **Natural Language Interface** - Chat with HubMind using plain English
- **Value Scoring** - Automatically score PRs by engagement and code changes
- **Trend Analysis** - Understand why repositories are trending
- **Controversy Detection** - Identify PRs with heated discussions
- **Similar Issue Detection** - Avoid creating duplicate issues
- **Developer Dashboard** - Monitor multiple repositories at once
- **Weekly Reports** - Generate activity summaries

## 📦 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 14+ (用于 Web 版用户认证和设置存储)
- GitHub Personal Access Token
- LLM API Key (支持多种提供商，见下方说明)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd HubMind
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
GITHUB_TOKEN=your_github_personal_access_token_here

# LLM Provider (默认: deepseek, 支持: deepseek, openai, anthropic, google, azure, ollama, groq)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Getting a GitHub Token:**
- Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
- Generate a new token with `repo` scope

**LLM Provider Options:**

HubMind 支持多种 LLM 提供商：

1. **DeepSeek** ⭐ (默认) - 需要 `DEEPSEEK_API_KEY`，性价比高，中文和代码能力强
2. **OpenAI** - 需要 `OPENAI_API_KEY`
3. **Anthropic Claude** - 需要 `ANTHROPIC_API_KEY`，安装：`pip install langchain-anthropic`
4. **Google Gemini** - 需要 `GOOGLE_API_KEY`，安装：`pip install langchain-google-genai`
5. **Azure OpenAI** - 需要 `AZURE_OPENAI_API_KEY` 和 `AZURE_OPENAI_ENDPOINT`
6. **Ollama** (本地) - 无需 API key，安装：`pip install langchain-ollama`
7. **Groq** - 需要 `GROQ_API_KEY`，安装：`pip install langchain-groq`

详细说明请查看：
- [LLM_SUPPORT.md](LLM_SUPPORT.md) - 所有 LLM 提供商配置
- [docs/DEEPSEEK.md](docs/DEEPSEEK.md) - DeepSeek 快速配置指南

**PostgreSQL 配置（Web 版必需）：**

HubMind Web 版使用 PostgreSQL 存储用户账号和设置。如果只使用 CLI 版本，可以跳过此步骤。

快速安装 PostgreSQL：

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE hubmind;"
sudo -u postgres psql -c "CREATE USER hubmind_user WITH PASSWORD 'hubmind_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hubmind TO hubmind_user;"
```

在 `backend/.env` 中配置：

```env
DATABASE_URL=postgresql://hubmind_user:hubmind_pass@localhost:5432/hubmind
```

详细说明请查看 [docs/POSTGRESQL.md](docs/POSTGRESQL.md)

## 🎮 Usage

### Command Line Interface

HubMind provides a rich CLI interface using Typer and Rich.

#### Get Trending Repositories

```bash
# Get today's top 10 trending repos
python main.py trending

# Filter by language
python main.py trending --language python

# Weekly trending
python main.py trending --since weekly --limit 20
```

#### Analyze Pull Requests

```bash
# Get today's PRs for a repository
python main.py prs microsoft/vscode

# Get most valuable PRs
python main.py prs microsoft/vscode --valuable

# Analyze a specific PR
python main.py analyze-pr microsoft/vscode 12345
```

#### Create Issues

```bash
# Create an issue from natural language
python main.py create-issue microsoft/vscode "Add dark mode support for the editor"

# With assignees and labels
python main.py create-issue facebook/react "Fix memory leak" --assignees "user1,user2" --labels "bug,urgent"
```

#### Chat with HubMind

```bash
# Single question
python main.py chat "Show me today's top 5 trending Python projects"

# Interactive mode
python main.py interactive
```

#### Ask Questions About Repositories

```bash
# Ask about a repository
python main.py ask microsoft/vscode "What build tool does this project use?"

python main.py ask facebook/react "How many contributors does this project have?"
```

#### Repository Health

```bash
# Get health metrics
python main.py health microsoft/vscode

# Custom time range
python main.py health facebook/react --days 60
```

#### Watch Multiple Repositories

```bash
# Monitor activity
python main.py watch "microsoft/vscode,facebook/react,vercel/next.js" --hours 24
```

### Interactive Mode

启动交互式对话模式，使用自然语言与 HubMind 交流：

```bash
python main.py interactive
```

**对话示例：**

```
You: 给我看看今天最火的 5 个 Python 项目
HubMind: [显示 5 个热门 Python 项目]

You: microsoft/vscode 今天有什么重要的 PR 吗？
HubMind: [显示有价值的 PR 列表]

You: 在 my-repo/awesome-project 创建一个 issue，说"添加 Python 3.12 支持"
HubMind: [创建 issue 并显示结果]

You: 那 Python 的呢？
HubMind: [基于上下文，显示 Python 热门项目]
```

**对话模式优势：**
- 自然语言交互，无需记住具体命令格式
- 上下文理解，可以基于之前的对话继续提问
- 智能解析，自动理解意图并调用合适的工具

## 🏗️ Architecture

### Project Structure

```
HubMind/
├── main.py                 # CLI entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── src/
│   ├── agents/
│   │   ├── hubmind_agent.py    # Main LangChain agent
│   │   └── qa_agent.py         # Q&A agent
│   ├── tools/
│   │   ├── github_trending.py  # Trending repositories tool
│   │   ├── github_pr.py        # PR analysis tool
│   │   └── github_issue.py     # Issue management tool
│   └── utils/
│       ├── dashboard.py        # Dashboard utilities
│       └── automation.py      # Automation workflows
└── README.md
```

### Key Components

1. **HubMindAgent** - Main agent powered by LangChain, orchestrates all tools
2. **GitHub Tools** - Direct GitHub API integrations for trending, PRs, issues
3. **QA Agent** - Specialized agent for answering repository questions
4. **Dashboard** - Health monitoring and activity tracking
5. **Automation** - Batch operations and workflow automation

## 🔧 API Reference

### GitHubTrendingTool

```python
from src.tools.github_trending import GitHubTrendingTool

tool = GitHubTrendingTool()
repos = tool.get_trending_repos(language="python", since="daily", limit=10)
```

### GitHubPRTool

```python
from src.tools.github_pr import GitHubPRTool

tool = GitHubPRTool()
prs = tool.get_valuable_prs("microsoft/vscode", limit=10)
analysis = tool.analyze_pr("microsoft/vscode", 12345)
```

### GitHubIssueTool

```python
from src.tools.github_issue import GitHubIssueTool

tool = GitHubIssueTool()
result = tool.create_issue_from_text(
    "microsoft/vscode",
    "Add support for Python 3.12"
)
```

### HubMindAgent

```python
from src.agents.hubmind_agent import HubMindAgent

agent = HubMindAgent()
response = agent.chat("Show me trending Python projects")
```

## 📊 Features in Detail

### 1. Trend Discovery Module

- **Daily/Weekly/Monthly trending** - Filter by time range
- **Language filtering** - Find trending repos in specific languages
- **Trend analysis** - Understand why repositories are trending
- **Summary generation** - Automatic summaries of trending repos

### 2. PR Analysis Module

- **Value scoring** - Automatic scoring based on engagement and changes
- **Today's PRs** - Get all PRs updated today
- **Detailed analysis** - File changes, reviews, maintainer participation
- **Controversy detection** - Identify PRs with heated discussions

### 3. Issue Management Module

- **Natural language creation** - Create issues from plain text
- **Auto-classification** - Automatically classify as bug/feature/docs
- **Similar issue detection** - Avoid duplicates
- **Smart labeling** - Automatic label suggestions

### 4. Smart Q&A Module

- **Repository questions** - Ask about any repository
- **Code questions** - Questions about code structure
- **Context-aware** - Uses README, commits, contributors for context

### 5. Developer Dashboard

- **Health metrics** - Issue response time, PR merge rate
- **Activity tracking** - Monitor multiple repositories
- **Contributor analysis** - Track active contributors
- **Commit frequency** - Analyze development velocity

### 6. Automation Workflows

- **Batch labeling** - Label multiple issues at once
- **Stale issue cleanup** - Close inactive issues
- **Contributor invitations** - Automate collaborator management
- **Weekly reports** - Generate activity summaries

## 🎨 Examples

### Example 1: Discover Trending Projects

```bash
python main.py trending --language rust --since weekly
```

### Example 2: Find Valuable PRs

```bash
python main.py prs facebook/react --valuable --limit 5
```

### Example 3: Create Issue from Text

```bash
python main.py create-issue my-org/my-repo "The login button doesn't work on mobile devices"
```

### Example 4: Interactive Chat

```bash
python main.py interactive
```

Then ask:
- "What are the top 5 trending JavaScript projects today?"
- "Show me the most valuable PRs in microsoft/vscode"
- "Create an issue in my-repo saying 'Add unit tests for authentication'"

### Example 5: Repository Health Check

```bash
python main.py health microsoft/vscode --days 30
```

## 🔒 安全注意事项

- **永远不要提交 `.env` 文件**到版本控制系统
- 妥善保管 GitHub token 和 LLM API keys
- 使用最小必要权限的 token
- 定期轮换 token
- 不要在公共场合分享 API keys

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🤖 LLM 支持

HubMind 支持多种 LLM 提供商，你可以根据需求选择：

- **DeepSeek** ⭐ (默认) - 性价比高，中文和代码能力强，[配置指南](docs/DEEPSEEK.md)
- **OpenAI** (GPT-4, GPT-3.5) - 高质量输出
- **Anthropic** (Claude) - 优秀的长文本处理
- **Google** (Gemini) - 性价比高
- **Azure OpenAI** - 企业级部署
- **Ollama** - 本地运行，完全免费
- **Groq** - 极速推理，免费额度

### 🎯 统一接口设计

HubMind 充分利用 **LangChain Model I/O** 模块，实现了**一份代码支持多个 LLM**：

- 所有 LLM 都实现 `BaseChatModel` 接口
- 业务代码只需写一份，无需为每个提供商单独实现
- 切换 LLM 只需改变 `provider` 参数
- 统一的调用接口：`invoke()`, `stream()`, `batch()` 等

**详细文档：**
- [LLM_SUPPORT.md](LLM_SUPPORT.md) - 各提供商详细配置说明
- [docs/DEEPSEEK.md](docs/DEEPSEEK.md) - DeepSeek 快速配置指南
- [docs/MODEL_IO.md](docs/MODEL_IO.md) - Model I/O 统一接口技术文档

## 🙏 Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Uses [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API
- CLI powered by [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- Supports multiple LLM providers for flexibility

## 📚 更多文档

- [QUICKSTART.md](QUICKSTART.md) - 5 分钟快速开始指南
- [WEB_README.md](WEB_README.md) - Web 界面使用指南
- [LLM_SUPPORT.md](LLM_SUPPORT.md) - LLM 提供商配置说明
- [docs/DEEPSEEK.md](docs/DEEPSEEK.md) - DeepSeek 配置指南
- [docs/POSTGRESQL.md](docs/POSTGRESQL.md) - PostgreSQL 详细配置
- [docs/POSTGRESQL_QUICK_SETUP.md](docs/POSTGRESQL_QUICK_SETUP.md) - PostgreSQL 快速安装
- [docs/MODEL_IO.md](docs/MODEL_IO.md) - Model I/O 技术文档
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

## 📧 支持

如有问题、建议或反馈，请在 GitHub 上提交 Issue。

---

**Made with ❤️ for the GitHub community**
