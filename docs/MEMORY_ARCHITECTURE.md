# HubMind 混合存储架构说明

## 概述

HubMind 使用 **Redis + PostgreSQL 混合存储**方案来管理对话历史，实现高性能和持久化的平衡。

## 架构设计

### 存储分层

```
┌─────────────────────────────────────────┐
│         用户对话请求                      │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  获取 session_id      │
    └──────────┬───────────┘
               │
    ┌──────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────┐            ┌──────────┐
│  Redis  │            │PostgreSQL│
│ (热数据)│            │  (冷数据) │
│ 24小时  │            │  永久存储 │
└────┬────┘            └─────┬────┘
     │                       │
     │ 滑动窗口加载           │ 历史数据
     │ (最近30条)             │
     └───────────┬───────────┘
                 │
                 ▼
         ┌───────────────┐
         │  合并上下文    │
         │ (最多30条)     │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ LangChain     │
         │ Memory        │
         └───────────────┘
```

### 数据流向

1. **写入流程**：
   - 新消息 → Redis（热数据，TTL 24小时）
   - 新消息 → PostgreSQL（冷数据，永久存储）
   - 清除合并结果缓存

2. **读取流程**：
   - 先查合并结果缓存（Redis，TTL 1小时，访问时刷新）
   - 缓存未命中 → 从 Redis 加载最近消息
   - Redis 不足 → 从 PostgreSQL 补充历史消息
   - 合并后缓存结果

## 核心组件

### 1. ConversationCacheManager (`src/utils/cache_manager.py`)

**功能**：管理对话上下文的 Redis 缓存

**特性**：
- TTL：1小时
- 访问时自动刷新 TTL
- 自动降级（Redis 不可用时返回 None）

**配置**：
```python
class CacheConfig:
    CONTEXT_CACHE_TTL = 3600  # 1小时
    REFRESH_ON_ACCESS = True  # 访问时刷新TTL
    MAX_CACHE_SIZE = 1000     # 最多缓存1000个会话
```

### 2. HybridMemoryManager (`src/utils/memory_manager.py`)

**功能**：混合存储管理器，实现滑动窗口加载

**特性**：
- 滑动窗口：只加载最近 30 条消息
- 热数据：Redis（今天的数据，TTL 24小时）
- 冷数据：PostgreSQL（历史数据）
- 自动合并：Redis + PostgreSQL

**配置**：
```python
class MemoryConfig:
    SLIDING_WINDOW_SIZE = 30      # 滑动窗口大小
    REDIS_HOT_DATA_TTL = 86400    # Redis热数据TTL：24小时
```

### 3. HybridCheckpointer (`src/utils/langchain_checkpointer.py`)

**功能**：LangChain Redis Checkpointer 包装器

**特性**：
- 使用 LangGraph 的 `RedisSaver`
- 自动降级（Redis 不可用时使用 fallback）
- 集成混合存储管理器

## 配置

### 环境变量

在 `.env` 或 `backend/.env` 中添加：

```bash
# Redis 配置（可选，默认: redis://localhost:6379/0）
REDIS_URL=redis://localhost:6379/0
```

### 代码配置

在 `config.py` 中：

```python
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

## 使用方式

### Agent 初始化

Agent 会自动使用 checkpointer（如果可用）：

```python
from src.agents.hubmind_agent import HubMindAgent
from src.utils.langchain_checkpointer import create_checkpointer

# 创建 checkpointer
checkpointer = create_checkpointer()

# 创建 Agent（自动集成 checkpointer）
agent = HubMindAgent(checkpointer=checkpointer)
```

### API 调用

使用 `session_id` 作为 `thread_id`：

```python
# 在 API 中
session_id = request.session_id  # 从请求获取
agent.chat_stream(message, session_id=session_id)
```

### 保存消息

使用混合存储管理器：

```python
from src.utils.memory_manager import HybridMemoryManager

memory_manager = HybridMemoryManager(db_session=db)

# 保存消息（自动写入 Redis 和 PostgreSQL）
memory_manager.save_message(
    session_id=session_id,
    role="user",
    content=message,
    save_to_db=True
)
```

## 性能优化

### 1. 滑动窗口

只加载最近 30 条消息，避免长会话的性能问题：

```python
# 只加载最近30条
messages = memory_manager.load_recent_messages(session_id, max_messages=30)
```

### 2. 缓存策略

- **合并结果缓存**：TTL 1小时，访问时刷新
- **Redis 热数据**：TTL 24小时
- **自动降级**：Redis 不可用时直接查 PostgreSQL

### 3. 数据同步

- **写入**：同时写入 Redis 和 PostgreSQL
- **读取**：优先 Redis，不足时补充 PostgreSQL
- **缓存失效**：数据更新时自动清除缓存

## 注意事项

1. **Redis 可选**：如果 Redis 不可用，系统会自动降级到 PostgreSQL
2. **数据一致性**：写入时同时写入 Redis 和 PostgreSQL，确保一致性
3. **内存管理**：Redis list 自动限制大小，防止内存溢出
4. **TTL 刷新**：每次访问缓存时自动刷新 TTL，活跃会话保持更久

## 依赖安装

```bash
pip install redis>=5.0.0
pip install langgraph>=0.0.20
```

## 故障排查

### Redis 连接失败

如果 Redis 连接失败，系统会：
1. 记录警告日志
2. 自动降级到 PostgreSQL
3. 功能正常，但性能可能下降

### 检查 Redis 状态

```python
from src.utils.cache_manager import get_cache_manager

cache_manager = get_cache_manager()
if cache_manager.is_available():
    print("Redis is available")
else:
    print("Redis is not available, using PostgreSQL only")
```

## 未来优化

1. **摘要功能**：对历史消息进行摘要，进一步减少数据量
2. **异步归档**：定期将 Redis 数据异步归档到 PostgreSQL
3. **LRU 缓存**：实现 LRU 策略清理不活跃的缓存
4. **分片存储**：对超长会话进行分片存储
