# 使用 DeepSeek API 运行 HubMind 项目

## ✅ 项目已准备就绪！

所有依赖已安装，代码已修复，可以直接运行。

## 🚀 快速开始

### 1. 配置环境变量

创建 `.env` 文件（如果还没有）：

```bash
cd /root/HubMind
cat > .env << 'EOF'
# GitHub API Configuration
GITHUB_TOKEN=your_github_personal_access_token_here

# LLM Provider Configuration (默认使用 DeepSeek)
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Optional
LOG_LEVEL=INFO
EOF
```

### 2. 获取 API Keys

#### GitHub Token
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择 `repo` 权限
4. 复制 token 并替换 `.env` 中的 `your_github_personal_access_token_here`

#### DeepSeek API Key
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key 并替换 `.env` 中的 `your_deepseek_api_key_here`

### 3. 验证配置

```bash
python3 -c "from config import Config; Config.validate(); print('✅ 配置验证成功！')"
```

### 4. 运行项目

#### 查看帮助
```bash
python3 main.py --help
```

#### 获取今日热门项目
```bash
python3 main.py trending
```

#### 查看某个项目的今日 PR
```bash
python3 main.py prs microsoft/vscode --valuable
```

#### 交互式聊天（推荐）
```bash
python3 main.py interactive
```

## 📝 示例命令

```bash
# 1. 查看今日热门 Python 项目
python3 main.py trending --language python --limit 10

# 2. 查看 React 项目今日最有价值的 PR
python3 main.py prs facebook/react --valuable

# 3. 分析特定 PR
python3 main.py analyze-pr facebook/react 12345

# 4. 询问仓库问题
python3 main.py ask microsoft/vscode "这个项目使用什么构建工具？"

# 5. 查看仓库健康度
python3 main.py health microsoft/vscode

# 6. 创建 Issue（需要仓库访问权限）
python3 main.py create-issue owner/repo "添加新功能：支持暗色模式"
```

## 💬 交互式模式示例

启动交互式模式后，你可以用自然语言与 HubMind 对话：

```
You: 给我看看今天最火的 5 个 Python 项目
HubMind: [显示结果]

You: microsoft/vscode 今天有什么重要的 PR 吗？
HubMind: [显示有价值的 PR]

You: 在 my-repo/awesome-project 创建一个 issue，说"添加单元测试"
HubMind: [创建 issue 并显示结果]
```

## ⚠️ 故障排除

### 错误: GITHUB_TOKEN is required
- 检查 `.env` 文件中是否设置了 `GITHUB_TOKEN`
- 确保 token 有效且有 `repo` 权限

### 错误: DEEPSEEK_API_KEY is required
- 检查 `.env` 文件中是否设置了 `DEEPSEEK_API_KEY`
- 确保 API Key 有效且有余额

### API 调用失败
- 检查网络连接
- 确认 API Key 有效
- 查看 DeepSeek 平台是否有服务状态问题

## 🎉 开始使用

现在你可以开始使用 HubMind 了！建议从交互式模式开始：

```bash
python3 main.py interactive
```

享受使用 HubMind 探索 GitHub 的乐趣！
