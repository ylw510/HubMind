"""
Redis Cache Manager for Conversation Context
支持 TTL 1小时，访问时自动刷新
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Redis 是必需依赖，用于记忆功能
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    raise ImportError(
        "redis module is required for memory functionality. "
        "Please install it with: pip install redis>=5.0.0"
    )


class CacheConfig:
    """缓存配置"""
    CONTEXT_CACHE_TTL = 3600  # 1小时
    REFRESH_ON_ACCESS = True  # 访问时刷新TTL
    MAX_CACHE_SIZE = 1000  # 最多缓存1000个会话
    REDIS_KEY_PREFIX = "conv_context:"  # Redis key前缀


class ConversationCacheManager:
    """对话上下文缓存管理器"""

    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL，格式: redis://localhost:6379/0
        """
        self.config = CacheConfig()

        # Redis 是必需的，如果不可用应该已经在上层抛出异常
        if not REDIS_AVAILABLE or redis is None:
            raise RuntimeError(
                "Redis is required for memory functionality. "
                "Please install redis: pip install redis>=5.0.0"
            )

        # 从环境变量或配置获取Redis URL
        if redis_url:
            self.redis_url = redis_url
        else:
            # 尝试从环境变量或配置读取
            import os
            from config import Config
            self.redis_url = os.getenv("REDIS_URL", Config.REDIS_URL)

        try:
            # 解析Redis URL
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis cache connected: {self.redis_url}")
        except Exception as e:
            error_msg = (
                f"Redis connection failed: {e}. "
                "Redis is required for memory functionality. "
                f"Please ensure Redis is running and accessible at: {self.redis_url}"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    def _get_key(self, session_id: int) -> str:
        """生成Redis key"""
        return f"{self.config.REDIS_KEY_PREFIX}{session_id}"

    def get_context(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        获取对话上下文缓存

        Args:
            session_id: 会话ID

        Returns:
            缓存的上下文数据，如果不存在返回None
        """
        if not self.redis_client:
            raise RuntimeError("Redis client is not available. Redis is required for memory functionality.")

        try:
            key = self._get_key(session_id)
            cached_data = self.redis_client.get(key)

            if cached_data:
                # 刷新TTL（每次访问延长1小时）
                if self.config.REFRESH_ON_ACCESS:
                    self.redis_client.expire(key, self.config.CONTEXT_CACHE_TTL)

                return json.loads(cached_data)

            return None
        except Exception as e:
            logger.error(f"Error getting cache for session {session_id}: {e}")
            return None

    def set_context(self, session_id: int, context: Dict[str, Any]) -> bool:
        """
        设置对话上下文缓存

        Args:
            session_id: 会话ID
            context: 上下文数据

        Returns:
            是否成功
        """
        if not self.redis_client:
            raise RuntimeError("Redis client is not available. Redis is required for memory functionality.")

        try:
            key = self._get_key(session_id)
            data_str = json.dumps(context, ensure_ascii=False)

            # 设置缓存，TTL 1小时
            self.redis_client.setex(
                key,
                self.config.CONTEXT_CACHE_TTL,
                data_str
            )

            return True
        except Exception as e:
            logger.error(f"Error setting cache for session {session_id}: {e}")
            return False

    def delete_context(self, session_id: int) -> bool:
        """
        删除对话上下文缓存

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if not self.redis_client:
            raise RuntimeError("Redis client is not available. Redis is required for memory functionality.")

        try:
            key = self._get_key(session_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for session {session_id}: {e}")
            return False

    def refresh_ttl(self, session_id: int) -> bool:
        """
        刷新缓存的TTL

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if not self.redis_client:
            raise RuntimeError("Redis client is not available. Redis is required for memory functionality.")

        try:
            key = self._get_key(session_id)
            if self.redis_client.exists(key):
                self.redis_client.expire(key, self.config.CONTEXT_CACHE_TTL)
                return True
            return False
        except Exception as e:
            logger.error(f"Error refreshing TTL for session {session_id}: {e}")
            return False

    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self.redis_client is not None


# 全局缓存管理器实例
_cache_manager: Optional[ConversationCacheManager] = None


def get_cache_manager() -> ConversationCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ConversationCacheManager()
    return _cache_manager
