# 查看 Redis 数据指南

本文档介绍如何查看 HubMind 项目中存储在 Redis 中的对话数据。

## 方法一：使用 Python 脚本（推荐）

项目提供了一个便捷的 Python 脚本来查看 Redis 数据：

```bash
# 查看所有 keys
python3 scripts/view_redis_data.py

# 列出所有会话
python3 scripts/view_redis_data.py --list

# 查看指定会话的消息（例如会话 ID 21）
python3 scripts/view_redis_data.py --session 21

# 查看指定会话的上下文缓存
python3 scripts/view_redis_data.py --context 21

# 查看所有 keys 的详细信息
python3 scripts/view_redis_data.py --all-keys
```

## 方法二：使用 redis-cli 命令行工具

### 1. 连接到 Redis

```bash
redis-cli -h 127.0.0.1 -p 6379
```

### 2. 查看所有 keys

```bash
# 查看所有 keys
KEYS *

# 查看热数据 keys（对话消息）
KEYS hot_messages:*

# 查看上下文缓存 keys
KEYS conv_context:*
```

### 3. 查看指定会话的消息

```bash
# 查看会话 21 的所有消息
LRANGE hot_messages:21 0 -1

# 查看会话 21 的前 5 条消息
LRANGE hot_messages:21 0 4

# 查看会话 21 的消息数量
LLEN hot_messages:21

# 查看会话 21 的 TTL（剩余过期时间）
TTL hot_messages:21
```

### 4. 查看消息内容（JSON 格式）

消息以 JSON 格式存储，每条消息包含 `role` 和 `content` 字段：

```bash
# 获取第一条消息并格式化
redis-cli -h 127.0.0.1 -p 6379 LRANGE hot_messages:21 0 0 | python3 -m json.tool
```

### 5. 查看上下文缓存

```bash
# 查看会话 21 的上下文缓存
GET conv_context:21

# 格式化 JSON 输出
redis-cli -h 127.0.0.1 -p 6379 GET conv_context:21 | python3 -m json.tool
```

## Redis Key 格式说明

### 热数据（对话消息）
- **Key 格式**: `hot_messages:{session_id}`
- **数据类型**: List (Redis List)
- **存储内容**: JSON 格式的消息列表
- **TTL**: 24 小时（86400 秒）
- **示例**: `hot_messages:21`

每条消息的 JSON 格式：
```json
{
  "role": "user",
  "content": "你好，我叫小明。"
}
```

或

```json
{
  "role": "assistant",
  "content": "你好小明！我是 HubMind..."
}
```

### 上下文缓存
- **Key 格式**: `conv_context:{session_id}`
- **数据类型**: String (JSON)
- **存储内容**: 对话上下文的缓存数据
- **TTL**: 1 小时（3600 秒），访问时自动刷新
- **示例**: `conv_context:21`

## 常用 Redis 命令

### 查看 Redis 信息
```bash
# 查看 Redis 服务器信息
INFO

# 查看 keyspace 信息
INFO keyspace

# 查看内存使用情况
INFO memory
```

### 删除数据（谨慎使用）
```bash
# 删除指定会话的热数据
DEL hot_messages:21

# 删除指定会话的上下文缓存
DEL conv_context:21

# 清空所有数据（危险！）
FLUSHDB
```

### 查看 TTL（剩余过期时间）
```bash
# 查看 key 的 TTL（秒）
TTL hot_messages:21

# -1 表示永不过期
# -2 表示 key 不存在
# 正数表示剩余秒数
```

## 方法三：使用 Redis GUI 工具

### RedisInsight（推荐）
- 下载地址: https://redis.com/redis-enterprise/redis-insight/
- 支持 Windows、macOS、Linux
- 提供图形化界面查看和管理 Redis 数据

### Another Redis Desktop Manager
- 开源免费的 Redis GUI 工具
- 支持 Windows、macOS、Linux
- GitHub: https://github.com/qishibo/AnotherRedisDesktopManager

## 示例：查看完整对话历史

```bash
# 1. 列出所有会话
python3 scripts/view_redis_data.py --list

# 2. 查看会话 21 的所有消息
python3 scripts/view_redis_data.py --session 21

# 3. 或者使用 redis-cli
redis-cli -h 127.0.0.1 -p 6379 LRANGE hot_messages:21 0 -1 | \
  python3 -c "import sys, json; \
    [print(f\"[{json.loads(line)['role'].upper()}]: {json.loads(line)['content'][:100]}\") \
     for line in sys.stdin if line.strip()]"
```

## 注意事项

1. **生产环境**: 在生产环境中查看 Redis 数据时，请确保有适当的权限和备份
2. **数据一致性**: Redis 中的数据是热数据（24小时TTL），完整的历史数据存储在 PostgreSQL 中
3. **不要手动修改**: 不建议手动修改 Redis 中的数据，可能导致数据不一致
4. **TTL 刷新**: 上下文缓存在访问时会自动刷新 TTL，确保活跃会话的缓存不会过期

## 故障排查

### 如果看不到数据
1. 检查 Redis 是否运行: `redis-cli -h 127.0.0.1 -p 6379 PING`
2. 检查 Redis URL 配置: `config.py` 中的 `REDIS_URL`
3. 检查是否有数据: `redis-cli -h 127.0.0.1 -p 6379 KEYS "*"`

### 如果数据过期了
- 热数据 TTL 为 24 小时，过期后会自动从 Redis 中删除
- 完整的历史数据仍然保存在 PostgreSQL 中
- 可以通过 `HybridMemoryManager.load_recent_messages()` 从 PostgreSQL 重新加载
