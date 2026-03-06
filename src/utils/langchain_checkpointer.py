"""
LangChain Checkpointer 包装器
使用 Redis 作为 LangChain 的 checkpointer 后端
"""
from typing import Any, Dict, Optional, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.cache_manager import get_cache_manager

logger = get_logger(__name__)

try:
    from langgraph.checkpoint.redis import RedisSaver
    from langgraph.checkpoint.base import Checkpoint
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("langgraph.checkpoint.redis not available. Install langgraph with redis support.")


class HybridCheckpointer:
    """
    混合 Checkpointer：Redis（热数据）+ PostgreSQL（冷数据）
    包装 LangChain 的 RedisSaver，并集成混合存储管理器
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化混合 Checkpointer

        Args:
            redis_url: Redis连接URL
        """
        self.cache_manager = get_cache_manager()

        if not REDIS_AVAILABLE:
            logger.warning("LangGraph Redis checkpoint not available. Using fallback.")
            self.redis_saver = None
        else:
            try:
                # 使用 LangChain 的 RedisSaver
                if redis_url:
                    self.redis_saver = RedisSaver(redis_url)
                else:
                    import os
                    from config import Config
                    redis_url = os.getenv("REDIS_URL", Config.REDIS_URL)
                    self.redis_saver = RedisSaver(redis_url)

                logger.info("Hybrid checkpointer initialized with Redis")
            except Exception as e:
                logger.warning(f"Failed to initialize RedisSaver: {e}. Using fallback.")
                self.redis_saver = None

    def get_checkpointer(self):
        """
        获取 LangChain checkpointer 实例

        Returns:
            RedisSaver 实例或 None
        """
        return self.redis_saver

    def is_available(self) -> bool:
        """检查 checkpointer 是否可用"""
        return self.redis_saver is not None


def create_checkpointer(redis_url: Optional[str] = None):
    """
    创建 checkpointer 实例

    Args:
        redis_url: Redis连接URL（可选）

    Returns:
        HybridCheckpointer 实例
    """
    return HybridCheckpointer(redis_url)
