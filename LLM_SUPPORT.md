# HubMind LLM 支持说明

HubMind 支持多种 LLM 提供商，你可以根据需求选择合适的模型。

## 支持的 LLM 提供商

### 1. DeepSeek (默认) ⭐

**模型示例：**
- `deepseek-chat` (默认)
- `deepseek-coder`

**配置：**
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
```

**安装：**
```bash
# 使用 langchain-openai (已包含，DeepSeek 使用 OpenAI 兼容 API)
pip install langchain-openai
```

**获取 API Key：**
- 访问 https://platform.deepseek.com/
- 注册账号并创建 API key

**优势：**
- 性价比高，价格实惠
- 中文支持优秀
- 代码能力强大
- OpenAI 兼容 API，易于集成

### 2. OpenAI

**模型示例：**
- `gpt-4-turbo-preview` (默认)
- `gpt-4`
- `gpt-3.5-turbo`
- `gpt-4o`

**配置：**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

**安装：**
```bash
# 已包含在 requirements.txt 中
pip install langchain-openai
```

### 3. Anthropic Claude

**模型示例：**
- `claude-3-opus-20240229` (默认)
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

**配置：**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**安装：**
```bash
pip install langchain-anthropic
```

**获取 API Key：**
- 访问 https://console.anthropic.com/
- 创建 API key

### 4. Google Gemini

**模型示例：**
- `gemini-pro` (默认)
- `gemini-pro-vision`

**配置：**
```env
LLM_PROVIDER=google
GOOGLE_API_KEY=...
```

**安装：**
```bash
pip install langchain-google-genai
```

**获取 API Key：**
- 访问 https://makersuite.google.com/app/apikey
- 创建 API key

### 5. Azure OpenAI

**配置：**
```env
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
LLM_MODEL=gpt-4  # 你的 Azure 部署名称
```

**安装：**
```bash
# 使用 langchain-openai (已包含)
pip install langchain-openai
```

### 6. Ollama (本地模型)

**模型示例：**
- `llama2` (默认)
- `mistral`
- `codellama`
- `llama3`

**配置：**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama2
```

**安装：**
```bash
# 1. 安装 Ollama
# macOS/Linux: https://ollama.ai/download
# 或使用: curl -fsSL https://ollama.ai/install.sh | sh

# 2. 下载模型
ollama pull llama2

# 3. 安装 Python 包
pip install langchain-ollama
```

**优势：**
- 完全本地运行，无需 API key
- 数据隐私保护
- 免费使用

### 7. Groq

**模型示例：**
- `mixtral-8x7b-32768` (默认)
- `llama2-70b-4096`
- `gemma-7b-it`

**配置：**
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

**安装：**
```bash
pip install langchain-groq
```

**获取 API Key：**
- 访问 https://console.groq.com/
- 创建 API key

**优势：**
- 极快的推理速度
- 免费额度

## 使用方法

### 方法 1: 环境变量配置（推荐）

在 `.env` 文件中设置：

```env
# DeepSeek (默认)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...

# 或使用其他提供商
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### 方法 2: 代码中指定

```python
from src.agents.hubmind_agent import HubMindAgent

# 使用 DeepSeek (默认)
agent = HubMindAgent(
    provider="deepseek",
    model_name="deepseek-chat"
)

# 使用 Anthropic Claude
agent = HubMindAgent(
    provider="anthropic",
    model_name="claude-3-sonnet-20240229"
)

# 使用 Google Gemini
agent = HubMindAgent(
    provider="google",
    model_name="gemini-pro"
)

# 使用 Ollama (本地)
agent = HubMindAgent(
    provider="ollama",
    model_name="llama2"
)
```

### 方法 3: CLI 参数（未来支持）

```bash
# 计划支持
python main.py chat --provider anthropic "Show me trending repos"
```

## 模型对比

| 提供商 | 速度 | 成本 | 质量 | 适用场景 |
|--------|------|------|------|----------|
| **DeepSeek** ⭐ | 快 | **低** | 高 | **中文场景、代码生成、性价比首选** |
| OpenAI GPT-4 | 中等 | 高 | 极高 | 复杂任务、高质量输出 |
| Anthropic Claude | 中等 | 高 | 极高 | 长文本、安全要求高 |
| Google Gemini | 快 | 中等 | 高 | 多模态、性价比 |
| Ollama | 快（本地） | 免费 | 中等 | 隐私敏感、离线使用 |
| Groq | 极快 | 免费/低 | 中等 | 快速响应、开发测试 |
| Azure OpenAI | 中等 | 高 | 极高 | 企业级、合规要求 |

## 推荐配置

### 开发/测试
```env
LLM_PROVIDER=deepseek  # 或 groq, ollama
DEEPSEEK_API_KEY=sk-...
```
- 快速响应
- 成本低
- 中文支持好

### 生产环境（推荐）
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
LLM_MODEL=deepseek-chat
```
- 性价比高
- 中文和代码能力强
- 稳定可靠

### 生产环境（高质量需求）
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```
- 高质量输出
- 稳定可靠

### 隐私敏感场景
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama2
```
- 完全本地
- 数据不出本地

### 长文本处理
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
```
- 超长上下文
- 优秀的长文本理解

## 故障排除

### 错误: ModuleNotFoundError

**问题：** 缺少对应提供商的包

**解决：**
```bash
# 安装对应的包
pip install langchain-anthropic  # 对于 Anthropic
pip install langchain-google-genai  # 对于 Google
pip install langchain-ollama  # 对于 Ollama
pip install langchain-groq  # 对于 Groq
```

### 错误: API key required

**问题：** 缺少 API key

**解决：**
1. 检查 `.env` 文件中的 API key 配置
2. 确保 API key 正确且有效
3. 对于 Ollama，确保服务正在运行：`ollama serve`

### 错误: Unsupported provider

**问题：** 使用了不支持的提供商名称

**解决：**
- 检查拼写：`openai`, `anthropic`, `google`, `azure`, `ollama`, `groq`
- 确保使用小写

## 性能优化建议

1. **本地开发**：使用 Ollama 或 Groq，快速且免费
2. **生产环境**：使用 OpenAI 或 Anthropic，质量更高
3. **批量处理**：考虑使用 Groq 的快速推理
4. **成本控制**：根据任务复杂度选择合适的模型

## 扩展支持

要添加新的 LLM 提供商：

1. 在 `src/utils/llm_factory.py` 中添加新的创建方法
2. 在 `config.py` 中添加对应的配置项
3. 更新本文档

## 更多信息

- [LangChain 文档](https://python.langchain.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
- [Google Gemini](https://ai.google.dev/)
- [Ollama](https://ollama.ai/)
- [Groq](https://groq.com/)
