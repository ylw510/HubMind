# HubMind Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```env
GITHUB_TOKEN=ghp_your_token_here

# DeepSeek (默认，推荐)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your_deepseek_key_here

# 或使用其他提供商
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your_openai_key_here
```

### Step 3: Test Installation

```bash
# Test trending repos
python main.py trending --limit 5

# Test interactive mode
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

## ⚠️ Troubleshooting

### Error: GITHUB_TOKEN is required
- Make sure you created a `.env` file
- Check that your token has `repo` scope

### Error: DEEPSEEK_API_KEY is required (或其他 LLM API key)
- Add your DeepSeek API key to `.env` (默认)
- 或添加其他 LLM 提供商的 API key
- 确保 API key 有效且有余额

### Error: Rate limit exceeded
- GitHub API has rate limits
- Wait a few minutes and try again
- Consider using a token with higher rate limits

### Import errors
- Make sure you're in the project root directory
- Run: `pip install -r requirements.txt`

## 💡 Tips

- Use `--help` with any command to see options
- Interactive mode remembers conversation context
- Value scores help identify important PRs
- Similar issue detection prevents duplicates

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples.py](examples.py) for programmatic usage
- Explore all commands with `python main.py --help`
