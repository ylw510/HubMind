"""
HubMind Configuration Module
"""
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Config:
    """Application configuration"""

    # GitHub API
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_API_BASE_URL: str = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")  # deepseek, openai, anthropic, google, azure, ollama, groq, openai_compatible
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")  # Optional: override default model

    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Google API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # Ollama (local)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # DeepSeek API (OpenAI compatible)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # 自定义 / OpenAI 兼容 API（provider=openai_compatible 时使用）
    OPENAI_COMPATIBLE_BASE_URL: str = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
    OPENAI_COMPATIBLE_API_KEY: str = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
    OPENAI_COMPATIBLE_MODEL: str = os.getenv("OPENAI_COMPATIBLE_MODEL", "")  # 或使用 LLM_MODEL

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Default settings
    DEFAULT_TRENDING_LIMIT: int = 10
    DEFAULT_PR_LIMIT: int = 20
    DEFAULT_ISSUE_LIMIT: int = 20

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.GITHUB_TOKEN:
            raise ValueError("请在「设置」中配置 GitHub Token（或在本机 .env 中设置 GITHUB_TOKEN）")

        # Validate LLM provider API key
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("请在「设置」中配置 LLM API Key（OpenAI），或设置 OPENAI_API_KEY")
        elif cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("请在「设置」中配置 LLM API Key（Anthropic），或设置 ANTHROPIC_API_KEY")
        elif cls.LLM_PROVIDER == "google" and not cls.GOOGLE_API_KEY:
            raise ValueError("请在「设置」中配置 LLM API Key（Google），或设置 GOOGLE_API_KEY")
        elif cls.LLM_PROVIDER == "azure":
            if not cls.AZURE_OPENAI_API_KEY:
                raise ValueError("请在「设置」中配置 LLM API Key（Azure），或设置 AZURE_OPENAI_API_KEY")
            if not cls.AZURE_OPENAI_ENDPOINT:
                raise ValueError("请设置 AZURE_OPENAI_ENDPOINT")
        elif cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("请在「设置」中配置 LLM API Key（Groq），或设置 GROQ_API_KEY")
        elif cls.LLM_PROVIDER == "deepseek" and not cls.DEEPSEEK_API_KEY:
            raise ValueError("请在「设置」中配置 LLM API Key（DeepSeek），或设置 DEEPSEEK_API_KEY")
        elif cls.LLM_PROVIDER == "openai_compatible":
            if not cls.OPENAI_COMPATIBLE_BASE_URL:
                raise ValueError("请在「设置」中选择「自定义(OpenAI 兼容)」并填写 API 地址，或设置 OPENAI_COMPATIBLE_BASE_URL")
            if not cls.OPENAI_COMPATIBLE_API_KEY:
                raise ValueError("请在「设置」中配置 LLM API Key（自定义 API），或设置 OPENAI_COMPATIBLE_API_KEY")
            if not (cls.OPENAI_COMPATIBLE_MODEL or cls.LLM_MODEL):
                raise ValueError("请在「设置」中填写模型名称，或设置 OPENAI_COMPATIBLE_MODEL / LLM_MODEL")
        # Ollama doesn't require API key (local)

        return True
