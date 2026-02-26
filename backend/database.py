"""
HubMind Backend - PostgreSQL database and SQLAlchemy models
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 确保可被单独运行时加载 .env（如迁移脚本）
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir.parent) not in sys.path:
    sys.path.insert(0, str(_backend_dir.parent))

from dotenv import load_dotenv
# 使用绝对路径并覆盖已有环境变量，确保 backend/.env 中的 DATABASE_URL 生效
_env_path = _backend_dir / ".env"
load_dotenv(_env_path, override=True)

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

def _url_has_password(url: str) -> bool:
    # postgresql://user:password@host → 前半段含 ":" 即表示有密码
    return bool(url and "@" in url and ":" in url.split("@")[0])

# 优先从 backend/.env 文件读取 DATABASE_URL，避免通过 start.sh 启动时环境变量被覆盖或未继承
DATABASE_URL = ""
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lstrip("\ufeff")
        if line.startswith("DATABASE_URL="):
            DATABASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'").strip()
            break
        if line.startswith("POSTGRES_URL="):
            DATABASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'").strip()
            break
if not DATABASE_URL or not _url_has_password(DATABASE_URL):
    DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "").strip()).strip()

if not DATABASE_URL:
    raise RuntimeError(
        "未配置 DATABASE_URL 或 POSTGRES_URL。"
        "请在 backend/.env 中设置，例如: DATABASE_URL=postgresql://user:password@localhost:5432/hubmind"
    )

# 连接池，适合多并发
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    github_token = Column(Text, default="")
    llm_provider = Column(String(32), default="deepseek")
    llm_api_key = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖：返回 DB 会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
