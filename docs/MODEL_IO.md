# LangChain Model I/O 统一接口说明

HubMind 充分利用 LangChain 的 Model I/O 模块，实现了**一份代码支持多个 LLM**的设计。

## 核心设计理念

### 1. 统一的 BaseChatModel 接口

所有 LLM 提供商都实现 LangChain 的 `BaseChatModel` 接口，这意味着：

```python
from langchain_core.language_models import BaseChatModel

# 无论使用哪个提供商，都返回 BaseChatModel
llm_openai = LLMFactory.create_llm(provider="openai")
llm_claude = LLMFactory.create_llm(provider="anthropic")
llm_ollama = LLMFactory.create_llm(provider="ollama")

# 所有 LLM 都支持相同的接口
response1 = llm_openai.invoke("Hello")
response2 = llm_claude.invoke("Hello")
response3 = llm_ollama.invoke("Hello")
```

### 2. 代码复用

由于所有 LLM 都实现相同的接口，业务代码只需要写一份：

```python
class HubMindAgent:
    def __init__(self, provider="openai"):
        # 同一份代码，支持所有提供商
        self.llm = LLMFactory.create_llm(provider=provider)

    def chat(self, message: str):
        # 使用统一的接口，无需关心底层实现
        return self.llm.invoke(message)
```

### 3. 无缝切换

切换 LLM 提供商只需要改变一个参数：

```python
# 使用 OpenAI
agent = HubMindAgent(provider="openai")

# 切换到 Claude
agent = HubMindAgent(provider="anthropic")

# 切换到本地 Ollama
agent = HubMindAgent(provider="ollama")

# 所有代码保持不变！
```

## LangChain Model I/O 的优势

### 1. 统一的调用接口

所有 LLM 都支持：
- `invoke()` - 同步调用
- `ainvoke()` - 异步调用
- `stream()` - 流式输出
- `astream()` - 异步流式输出
- `batch()` - 批量处理

```python
# 同步调用
response = llm.invoke("Hello")

# 异步调用
response = await llm.ainvoke("Hello")

# 流式输出
for chunk in llm.stream("Hello"):
    print(chunk)

# 批量处理
responses = llm.batch(["Hello", "World"])
```

### 2. 统一的消息格式

所有 LLM 使用相同的消息格式：

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant"),
    HumanMessage(content="Hello"),
    AIMessage(content="Hi there!"),
]

response = llm.invoke(messages)
```

### 3. 统一的工具调用

支持工具调用的 LLM 可以使用统一的接口：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather in {city}: Sunny"

# 绑定工具
llm_with_tools = llm.bind_tools([get_weather])

# 调用
response = llm_with_tools.invoke("What's the weather in Beijing?")
```

## 实现细节

### LLMFactory 设计

```python
class LLMFactory:
    """利用 LangChain Model I/O 统一接口"""

    @staticmethod
    def create_llm(provider: str, ...) -> BaseChatModel:
        """
        返回 BaseChatModel，确保所有提供商行为一致
        """
        # 所有提供商都返回 BaseChatModel
        if provider == "openai":
            return ChatOpenAI(...)  # 继承 BaseChatModel
        elif provider == "anthropic":
            return ChatAnthropic(...)  # 继承 BaseChatModel
        # ...
```

### Agent 创建

```python
class HubMindAgent:
    def _create_agent(self):
        """
        使用统一的 BaseChatModel 接口创建 Agent
        自动适配不同 LLM 的能力
        """
        # 尝试使用工具调用（支持 OpenAI, Anthropic 等）
        if self._supports_tool_calling():
            return create_tool_calling_agent(self.llm, self.tools, prompt)
        else:
            # 回退到 ReAct（支持所有 LLM）
            return create_react_agent(self.llm, self.tools, prompt)
```

## 支持的 LLM 提供商

所有提供商都通过 `BaseChatModel` 接口统一：

| 提供商 | 类名 | 继承自 |
|--------|------|--------|
| DeepSeek ⭐ | `ChatOpenAI` (with base_url) | `BaseChatModel` |
| OpenAI | `ChatOpenAI` | `BaseChatModel` |
| Anthropic | `ChatAnthropic` | `BaseChatModel` |
| Google | `ChatGoogleGenerativeAI` | `BaseChatModel` |
| Azure | `AzureChatOpenAI` | `BaseChatModel` |
| Ollama | `ChatOllama` | `BaseChatModel` |
| Groq | `ChatGroq` | `BaseChatModel` |

## 使用示例

### 示例 1: 切换提供商

```python
# 开发环境使用本地模型
agent_dev = HubMindAgent(provider="ollama")

# 生产环境使用 OpenAI
agent_prod = HubMindAgent(provider="openai")

# 代码完全相同！
response = agent_dev.chat("Show trending repos")
response = agent_prod.chat("Show trending repos")
```

### 示例 2: 批量测试不同模型

```python
providers = ["openai", "anthropic", "groq", "ollama"]

for provider in providers:
    llm = LLMFactory.create_llm(provider=provider)
    response = llm.invoke("Hello")
    print(f"{provider}: {response.content}")
```

### 示例 3: 流式输出

```python
llm = LLMFactory.create_llm(provider="openai")

# 所有提供商都支持流式输出
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

## 优势总结

1. **代码复用** - 一份代码支持所有 LLM
2. **易于切换** - 只需改变 provider 参数
3. **统一接口** - 所有 LLM 行为一致
4. **类型安全** - 都返回 `BaseChatModel`
5. **易于测试** - 可以轻松替换为 mock
6. **未来扩展** - 添加新提供商只需实现 `BaseChatModel`

## 最佳实践

1. **始终使用 BaseChatModel 类型注解**
   ```python
   def process(llm: BaseChatModel):
       return llm.invoke("Hello")
   ```

2. **通过配置切换提供商**
   ```python
   # .env
   LLM_PROVIDER=openai
   ```

3. **使用统一的错误处理**
   ```python
   try:
       response = llm.invoke(message)
   except Exception as e:
       # 所有 LLM 的错误处理方式相同
       handle_error(e)
   ```

4. **利用 LangChain 的链式调用**
   ```python
   from langchain.chains import LLMChain

   chain = LLMChain(llm=llm, prompt=prompt)
   # 适用于所有 LLM
   ```

## 参考资源

- [LangChain Model I/O 文档](https://python.langchain.com/docs/modules/model_io/)
- [BaseChatModel API](https://api.python.langchain.com/en/latest/langchain_core/langchain_core.language_models.chat_models.BaseChatModel.html)
- [LangChain 工具调用](https://python.langchain.com/docs/modules/model_io/chat/function_calling/)
