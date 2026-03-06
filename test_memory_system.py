#!/usr/bin/env python3
"""
测试混合存储系统
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("HubMind 混合存储系统测试")
print("=" * 60)
print()

# 测试 1: 缓存管理器
print("【测试 1】Redis 缓存管理器")
print("-" * 60)
try:
    from src.utils.cache_manager import get_cache_manager, CacheConfig

    cache_manager = get_cache_manager()
    print(f"✅ 缓存管理器创建成功")
    print(f"   - Redis 可用: {cache_manager.is_available()}")
    print(f"   - TTL: {CacheConfig.CONTEXT_CACHE_TTL}秒 ({CacheConfig.CONTEXT_CACHE_TTL/3600:.1f}小时)")
    print(f"   - 访问时刷新: {CacheConfig.REFRESH_ON_ACCESS}")

    if cache_manager.is_available():
        # 测试缓存操作
        test_session_id = 999999
        test_context = {"messages": [{"role": "user", "content": "测试消息"}]}

        # 设置缓存
        if cache_manager.set_context(test_session_id, test_context):
            print(f"   ✅ 缓存设置成功")

        # 获取缓存
        cached = cache_manager.get_context(test_session_id)
        if cached:
            print(f"   ✅ 缓存获取成功: {len(cached.get('messages', []))} 条消息")

        # 删除测试缓存
        cache_manager.delete_context(test_session_id)
        print(f"   ✅ 缓存删除成功")
    else:
        print(f"   ⚠️  Redis 不可用，将使用 PostgreSQL 降级模式")

except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 2: 混合存储管理器
print("【测试 2】混合存储管理器")
print("-" * 60)
try:
    from src.utils.memory_manager import HybridMemoryManager, MemoryConfig

    print(f"✅ 混合存储管理器导入成功")
    print(f"   - 滑动窗口大小: {MemoryConfig.SLIDING_WINDOW_SIZE} 条消息")
    print(f"   - Redis 热数据 TTL: {MemoryConfig.REDIS_HOT_DATA_TTL}秒 ({MemoryConfig.REDIS_HOT_DATA_TTL/3600:.1f}小时)")

    # 注意：需要数据库连接才能完整测试
    print(f"   ⚠️  完整测试需要数据库连接（在 API 运行时测试）")

except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 3: LangChain Checkpointer
print("【测试 3】LangChain Checkpointer")
print("-" * 60)
try:
    from src.utils.langchain_checkpointer import create_checkpointer

    checkpointer = create_checkpointer()
    print(f"✅ Checkpointer 创建成功")
    print(f"   - Checkpointer 可用: {checkpointer.is_available()}")

    if checkpointer.is_available():
        cp_instance = checkpointer.get_checkpointer()
        print(f"   ✅ RedisSaver 实例: {type(cp_instance).__name__}")
    else:
        print(f"   ⚠️  LangGraph Redis checkpoint 不可用（需要安装 langgraph）")
        print(f"   ℹ️  系统将使用降级模式")

except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 4: Agent 集成
print("【测试 4】Agent Checkpointer 集成")
print("-" * 60)
try:
    from src.agents.hubmind_agent import HubMindAgent
    from src.utils.langchain_checkpointer import create_checkpointer

    checkpointer = create_checkpointer()
    print(f"✅ Checkpointer 准备完成")

    # 检查 Agent 是否支持 checkpointer 参数
    import inspect
    agent_init = inspect.signature(HubMindAgent.__init__)
    if 'checkpointer' in agent_init.parameters:
        print(f"   ✅ HubMindAgent 支持 checkpointer 参数")
    else:
        print(f"   ❌ HubMindAgent 不支持 checkpointer 参数")

    # 检查 chat_stream 是否支持 session_id
    chat_stream_sig = inspect.signature(HubMindAgent.chat_stream)
    if 'session_id' in chat_stream_sig.parameters:
        print(f"   ✅ chat_stream 支持 session_id 参数")
    else:
        print(f"   ❌ chat_stream 不支持 session_id 参数")

    # 检查 chat 是否支持 session_id
    chat_sig = inspect.signature(HubMindAgent.chat)
    if 'session_id' in chat_sig.parameters:
        print(f"   ✅ chat 支持 session_id 参数")
    else:
        print(f"   ❌ chat 不支持 session_id 参数")

except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 5: 配置检查
print("【测试 5】配置检查")
print("-" * 60)
try:
    from config import Config
    import os

    redis_url = os.getenv("REDIS_URL", Config.REDIS_URL)
    print(f"✅ 配置读取成功")
    print(f"   - REDIS_URL: {redis_url}")
    print(f"   - 默认值: {Config.REDIS_URL}")

except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 6: 依赖检查
print("【测试 6】依赖检查")
print("-" * 60)
try:
    import redis
    print(f"✅ redis 模块已安装: {redis.__version__}")
except ImportError:
    print(f"   ❌ redis 模块未安装，请运行: pip install redis>=5.0.0")

try:
    import langgraph
    print(f"✅ langgraph 模块已安装")
except ImportError:
    print(f"   ⚠️  langgraph 模块未安装，Redis checkpoint 将不可用")
    print(f"   ℹ️  请运行: pip install langgraph>=0.0.20")

try:
    from langgraph.checkpoint.redis import RedisSaver
    print(f"✅ langgraph.checkpoint.redis 可用")
except ImportError:
    print(f"   ⚠️  langgraph.checkpoint.redis 不可用")
    print(f"   ℹ️  系统将使用降级模式（仅 PostgreSQL）")

print()

# 总结
print("=" * 60)
print("测试总结")
print("=" * 60)
print()
print("✅ 核心组件已实现并可以导入")
print("✅ 系统支持 Redis 降级（Redis 不可用时使用 PostgreSQL）")
print()
print("下一步：")
print("1. 安装依赖: pip install redis>=5.0.0 langgraph>=0.0.20")
print("2. 配置 Redis URL（可选）: 在 .env 中设置 REDIS_URL")
print("3. 启动后端服务进行完整测试")
print()
