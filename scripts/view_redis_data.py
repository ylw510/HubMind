#!/usr/bin/env python3
"""
查看 Redis 中的对话数据
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis
from config import Config
from src.utils.memory_manager import MemoryConfig
from src.utils.cache_manager import CacheConfig
import json

def print_separator():
    print("=" * 80)

def view_all_keys():
    """查看所有相关的 Redis keys"""
    print_separator()
    print("📋 查看所有 Redis Keys")
    print_separator()

    client = redis.from_url(Config.REDIS_URL, decode_responses=True)

    # 查找所有相关的 keys
    all_keys = client.keys("*")
    hot_keys = client.keys("hot_messages:*")
    context_keys = client.keys("conv_context:*")

    print(f"\n总共有 {len(all_keys)} 个 keys")
    print(f"热数据 (hot_messages:): {len(hot_keys)} 个")
    print(f"上下文缓存 (conv_context:): {len(context_keys)} 个")

    if hot_keys:
        print("\n🔥 热数据 Keys (对话消息):")
        for key in sorted(hot_keys):
            ttl = client.ttl(key)
            length = client.llen(key)
            print(f"  - {key} (消息数: {length}, TTL: {ttl}s)")

    if context_keys:
        print("\n💾 上下文缓存 Keys:")
        for key in sorted(context_keys):
            ttl = client.ttl(key)
            print(f"  - {key} (TTL: {ttl}s)")

    print()

def view_session_messages(session_id: int):
    """查看指定会话的消息"""
    print_separator()
    print(f"💬 查看会话 {session_id} 的消息")
    print_separator()

    client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    key = f"{MemoryConfig.REDIS_KEY_PREFIX}{session_id}"

    if not client.exists(key):
        print(f"❌ 会话 {session_id} 在 Redis 中不存在")
        return

    messages = client.lrange(key, 0, -1)
    print(f"\n找到 {len(messages)} 条消息:\n")

    for idx, msg_json in enumerate(messages, 1):
        try:
            msg = json.loads(msg_json)
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 截断长内容
            content_preview = content[:100] + "..." if len(content) > 100 else content
            print(f"{idx}. [{role.upper()}]")
            print(f"   {content_preview}")
            print()
        except json.JSONDecodeError:
            print(f"{idx}. [ERROR] 无法解析消息: {msg_json[:50]}...")
            print()

def view_context_cache(session_id: int):
    """查看指定会话的上下文缓存"""
    print_separator()
    print(f"💾 查看会话 {session_id} 的上下文缓存")
    print_separator()

    client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    key = f"{CacheConfig.REDIS_KEY_PREFIX}{session_id}"

    if not client.exists(key):
        print(f"❌ 会话 {session_id} 的上下文缓存在 Redis 中不存在")
        return

    cache_data = client.get(key)
    ttl = client.ttl(key)

    print(f"\nTTL: {ttl} 秒")
    print(f"\n缓存内容:")
    try:
        cache = json.loads(cache_data)
        print(json.dumps(cache, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(cache_data)

def list_all_sessions():
    """列出所有会话 ID"""
    print_separator()
    print("📋 列出所有会话")
    print_separator()

    client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    hot_keys = client.keys("hot_messages:*")

    if not hot_keys:
        print("❌ 没有找到任何会话")
        return

    print(f"\n找到 {len(hot_keys)} 个会话:\n")

    sessions = []
    for key in sorted(hot_keys):
        # 提取 session_id
        session_id = key.replace(MemoryConfig.REDIS_KEY_PREFIX, "")
        try:
            session_id_int = int(session_id)
            length = client.llen(key)
            ttl = client.ttl(key)
            sessions.append({
                "id": session_id_int,
                "key": key,
                "message_count": length,
                "ttl": ttl
            })
        except ValueError:
            continue

    # 按 session_id 排序
    sessions.sort(key=lambda x: x["id"])

    for sess in sessions:
        print(f"会话 ID: {sess['id']}")
        print(f"  消息数: {sess['message_count']}")
        print(f"  TTL: {sess['ttl']} 秒")
        print()

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="查看 Redis 中的对话数据")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有会话")
    parser.add_argument("--all-keys", "-a", action="store_true", help="查看所有 keys")
    parser.add_argument("--session", "-s", type=int, help="查看指定会话的消息")
    parser.add_argument("--context", "-c", type=int, help="查看指定会话的上下文缓存")

    args = parser.parse_args()

    if args.list:
        list_all_sessions()
    elif args.all_keys:
        view_all_keys()
    elif args.session:
        view_session_messages(args.session)
    elif args.context:
        view_context_cache(args.context)
    else:
        # 默认显示所有 keys
        view_all_keys()
        print("\n💡 使用提示:")
        print("  python scripts/view_redis_data.py --list          # 列出所有会话")
        print("  python scripts/view_redis_data.py --session 1    # 查看会话1的消息")
        print("  python scripts/view_redis_data.py --context 1     # 查看会话1的上下文缓存")
        print("  python scripts/view_redis_data.py --all-keys      # 查看所有 keys")

if __name__ == "__main__":
    main()
