"""
混合存储管理器：Redis（热数据）+ PostgreSQL（冷数据）
实现滑动窗口加载，只加载最近N条消息
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.cache_manager import get_cache_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryConfig:
    """内存管理配置"""
    SLIDING_WINDOW_SIZE = 30  # 滑动窗口大小：只加载最近30条消息
    REDIS_HOT_DATA_TTL = 86400  # Redis热数据TTL：24小时
    REDIS_KEY_PREFIX = "hot_messages:"  # Redis热数据key前缀


class HybridMemoryManager:
    """混合存储管理器：Redis（热数据）+ PostgreSQL（冷数据）"""

    def __init__(self, db_session=None):
        """
        初始化混合存储管理器

        Args:
            db_session: SQLAlchemy数据库会话（可选，用于查询PostgreSQL）
        """
        self.config = MemoryConfig()
        self.cache_manager = get_cache_manager()
        self.db_session = db_session

    def _get_redis_key(self, session_id: int) -> str:
        """生成Redis热数据key"""
        return f"{self.config.REDIS_KEY_PREFIX}{session_id}"

    def _format_message(self, role: str, content: str) -> Dict[str, str]:
        """格式化消息为统一格式"""
        return {
            "role": role,
            "content": content
        }

    def load_recent_messages(
        self,
        session_id: int,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        加载最近的消息（滑动窗口）

        Args:
            session_id: 会话ID
            max_messages: 最大消息数，默认使用配置的窗口大小

        Returns:
            消息列表，按时间顺序排列
        """
        max_messages = max_messages or self.config.SLIDING_WINDOW_SIZE

        # 1. 先尝试从缓存获取合并结果
        cached_context = self.cache_manager.get_context(session_id)
        if cached_context and "messages" in cached_context:
            messages = cached_context["messages"]
            if len(messages) >= max_messages:
                # 缓存中有足够的数据，直接返回最近的N条
                return messages[-max_messages:]

        # 2. 从Redis加载热数据（今天的数据）
        redis_messages = self._load_from_redis(session_id)

        # 3. 如果Redis数据不足，从PostgreSQL补充
        if len(redis_messages) < max_messages and self.db_session:
            needed = max_messages - len(redis_messages)
            pg_messages = self._load_from_postgres(session_id, limit=needed)

            # 合并：PostgreSQL（历史） + Redis（今天）
            all_messages = pg_messages + redis_messages
        else:
            all_messages = redis_messages

        # 4. 只返回最近的N条
        result = all_messages[-max_messages:] if len(all_messages) > max_messages else all_messages

        # 5. 缓存合并结果
        if result:
            self.cache_manager.set_context(session_id, {"messages": result})

        return result

    def _load_from_redis(self, session_id: int) -> List[Dict[str, str]]:
        """从Redis加载热数据（今天的数据）"""
        if not self.cache_manager.is_available():
            return []

        try:
            redis_client = self.cache_manager.redis_client
            key = self._get_redis_key(session_id)

            # 从Redis list获取消息（按时间顺序）
            messages_data = redis_client.lrange(key, 0, -1)

            messages = []
            for msg_data in messages_data:
                try:
                    msg = json.loads(msg_data)
                    messages.append(self._format_message(msg["role"], msg["content"]))
                except Exception as e:
                    logger.warning(f"Error parsing Redis message: {e}")
                    continue

            return messages
        except Exception as e:
            logger.error(f"Error loading from Redis for session {session_id}: {e}")
            return []

    def _load_from_postgres(self, session_id: int, limit: int) -> List[Dict[str, str]]:
        """从PostgreSQL加载冷数据（历史数据）"""
        if not self.db_session:
            return []

        try:
            from backend.database import ChatMessage

            # 查询最近的消息（排除今天的数据，因为今天的数据在Redis中）
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            messages = self.db_session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.created_at < today_start
            ).order_by(
                ChatMessage.created_at.desc()
            ).limit(limit).all()

            # 转换为统一格式（按时间正序）
            result = []
            for msg in reversed(messages):
                result.append(self._format_message(msg.role, msg.content))

            return result
        except Exception as e:
            logger.error(f"Error loading from PostgreSQL for session {session_id}: {e}")
            return []

    def save_message(
        self,
        session_id: int,
        role: str,
        content: str,
        save_to_db: bool = True
    ) -> bool:
        """
        保存消息到热数据（Redis）和冷数据（PostgreSQL）

        Args:
            session_id: 会话ID
            role: 消息角色（user/assistant）
            content: 消息内容
            save_to_db: 是否同时保存到PostgreSQL

        Returns:
            是否成功
        """
        message = self._format_message(role, content)

        # 1. 保存到Redis（热数据）
        if self.cache_manager.is_available():
            try:
                redis_client = self.cache_manager.redis_client
                key = self._get_redis_key(session_id)

                # 添加到Redis list
                redis_client.rpush(key, json.dumps(message))

                # 设置TTL（24小时）
                redis_client.expire(key, self.config.REDIS_HOT_DATA_TTL)

                # 限制list大小（只保留最近的消息）
                max_list_size = self.config.SLIDING_WINDOW_SIZE * 2  # 保留更多以应对并发
                current_size = redis_client.llen(key)
                if current_size > max_list_size:
                    # 删除最旧的消息
                    redis_client.ltrim(key, current_size - max_list_size, -1)
            except Exception as e:
                logger.error(f"Error saving to Redis for session {session_id}: {e}")

        # 2. 保存到PostgreSQL（冷数据，异步）
        if save_to_db and self.db_session:
            try:
                from backend.database import ChatMessage

                chat_msg = ChatMessage(
                    session_id=session_id,
                    role=role,
                    content=content
                )
                self.db_session.add(chat_msg)
                self.db_session.commit()
            except Exception as e:
                logger.error(f"Error saving to PostgreSQL for session {session_id}: {e}")
                if self.db_session:
                    self.db_session.rollback()

        # 3. 清除合并结果缓存（因为数据已更新）
        self.cache_manager.delete_context(session_id)

        return True

    def clear_cache(self, session_id: int) -> bool:
        """清除会话的缓存"""
        return self.cache_manager.delete_context(session_id)
