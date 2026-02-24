# DeepSeek API 运行指南

## 快速配置

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件，内容如下：

```env
# GitHub API Configuration
# 获取方式: https://github.com/settings/tokens (需要 repo 权限)
GITHUB_TOKEN=your_github_personal_access_token_here

# LLM Provider Configuration (默认使用 DeepSeek)
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# DeepSeek API Configuration
# 获取方式: https://platform.deepseek.com/ (注册并创建 API Key)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Optional
LOG_LEVEL=INFO
```

### 2. 获取 API Keys

#### GitHub Token
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择 `repo` 权限
4. 复制生成的 token

#### DeepSeek API Key
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行项目

#### 查看帮助
```bash
python main.py --help
```

#### 获取今日热门项目
```bash
python main.py trending
```

#### 查看某个项目的今日 PR
```bash
python main.py prs microsoft/vscode --valuable
```

#### 交互式聊天
```bash
python main.py interactive
```

#### 创建 Issue
```bash
python main.py create-issue owner/repo "添加新功能：支持暗色模式"
```

## 示例命令

```bash
# 1. 查看今日热门 Python 项目
python main.py trending --language python --limit 10

# 2. 查看 React 项目今日最有价值的 PR
python main.py prs facebook/react --valuable

# 3. 分析特定 PR
python main.py analyze-pr facebook/react 12345

# 4. 询问仓库问题
python main.py ask microsoft/vscode "这个项目使用什么构建工具？"

# 5. 查看仓库健康度
python main.py health microsoft/vscode

# 6. 交互式模式（推荐）
python main.py interactive
```

## 交互式模式示例

启动交互式模式后，你可以用自然语言与 HubMind 对话：

```
You: 给我看看今天最火的 5 个 Python 项目
HubMind: [显示结果]

You: microsoft/vscode 今天有什么重要的 PR 吗？
HubMind: [显示有价值的 PR]

You: 在 my-repo/awesome-project 创建一个 issue，说"添加单元测试"
HubMind: [创建 issue 并显示结果]
```

## 故障排除

### 错误: GITHUB_TOKEN is required
- 检查 `.env` 文件中是否设置了 `GITHUB_TOKEN`
- 确保 token 有效且有 `repo` 权限

### 错误: DEEPSEEK_API_KEY is required
- 检查 `.env` 文件中是否设置了 `DEEPSEEK_API_KEY`
- 确保 API Key 有效且有余额

### 错误: ModuleNotFoundError
- 运行 `pip install -r requirements.txt` 安装所有依赖

### API 调用失败
- 检查网络连接
- 确认 API Key 有效
- 查看 DeepSeek 平台是否有服务状态问题

## 验证配置

运行以下命令验证配置是否正确：

```bash
python -c "from config import Config; Config.validate(); print('配置验证成功！')"
```

如果看到 "配置验证成功！"，说明配置正确。
