# HubMind 对话模式使用示例

## 🎯 如何使用对话模式查找今天最火的5个项目

### 方法 1: 交互式对话模式（推荐）

#### 步骤 1: 启动交互式模式

```bash
python3 main.py interactive
```

#### 步骤 2: 在对话中输入自然语言

启动后，你会看到：
```
🤖 HubMind Interactive Mode
Type 'exit' or 'quit' to end the session

You:
```

#### 步骤 3: 输入你的问题

你可以用多种方式表达同一个需求：

**方式 1（简洁）：**
```
You: 给我看看今天最火的5个项目
```

**方式 2（详细）：**
```
You: 查找今天最热门的5个GitHub项目
```

**方式 3（指定语言）：**
```
You: 给我看看今天最火的5个Python项目
```

**方式 4（英文）：**
```
You: Show me the top 5 trending repositories today
```

#### 步骤 4: 查看结果

HubMind 会调用相应的工具，并返回格式化的结果，例如：

```
HubMind:
┌─────────────────────────────────────────────────────────┐
│ Found 5 trending repositories:                          │
│                                                         │
│ 1. **owner/repo1** (1234 ⭐)                          │
│    Description of the project                          │
│    Language: Python                                     │
│    URL: https://github.com/owner/repo1                 │
│                                                         │
│ 2. **owner/repo2** (987 ⭐)                            │
│    ...                                                  │
└─────────────────────────────────────────────────────────┘
```

### 方法 2: 单次对话模式

如果你只想问一个问题，可以使用 `chat` 命令：

```bash
python3 main.py chat "给我看看今天最火的5个项目"
```

或者：

```bash
python3 main.py chat "查找今天最热门的5个GitHub项目"
```

### 方法 3: 直接使用命令（非对话模式）

如果你知道具体命令，也可以直接使用：

```bash
# 查看今天最火的10个项目（默认）
python3 main.py trending --limit 10

# 查看今天最火的5个项目
python3 main.py trending --limit 5

# 查看今天最火的5个Python项目
python3 main.py trending --language python --limit 5
```

## 💡 对话模式的优势

1. **自然语言** - 不需要记住具体命令格式
2. **上下文理解** - 可以基于之前的对话继续提问
3. **智能解析** - HubMind 会自动理解你的意图并调用合适的工具

## 📝 更多对话示例

### 示例 1: 查找热门项目

```
You: 给我看看今天最火的5个项目
HubMind: [显示5个热门项目]

You: 那Python的呢？
HubMind: [显示5个Python热门项目]
```

### 示例 2: 分析PR

```
You: microsoft/vscode 今天有什么重要的PR吗？
HubMind: [显示有价值的PR列表]

You: 详细分析一下第一个PR
HubMind: [显示PR的详细分析]
```

### 示例 3: 创建Issue

```
You: 在 my-org/my-repo 创建一个issue，说"添加暗色模式支持"
HubMind: [创建issue并显示结果]
```

### 示例 4: 询问仓库信息

```
You: microsoft/vscode 这个项目用什么语言写的？
HubMind: [回答项目的主要编程语言]
```

## 🚀 快速开始

1. **确保已配置 API Keys**
   ```bash
   # 检查配置
   python3 -c "from config import Config; Config.validate(); print('✅ 配置正确')"
   ```

2. **启动交互式模式**
   ```bash
   python3 main.py interactive
   ```

3. **开始对话**
   ```
   You: 给我看看今天最火的5个项目
   ```

## ⚠️ 注意事项

- 确保已设置 `GITHUB_TOKEN` 和 `DEEPSEEK_API_KEY` 在 `.env` 文件中
- 对话模式需要网络连接来调用 GitHub API 和 DeepSeek API
- 输入 `exit` 或 `quit` 退出交互式模式
- 使用 `Ctrl+C` 也可以退出

## 🎉 开始使用

现在就试试吧！

```bash
python3 main.py interactive
```

然后输入：`给我看看今天最火的5个项目`
