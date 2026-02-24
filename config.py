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
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")  # deepseek, openai, anthropic, google, azure, ollama, groq
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
            raise ValueError("GITHUB_TOKEN is required. Please set it in .env file")

        # Validate LLM provider API key
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        elif cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic provider")
        elif cls.LLM_PROVIDER == "google" and not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when using Google provider")
        elif cls.LLM_PROVIDER == "azure":
            if not cls.AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEY is required when using Azure provider")
            if not cls.AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_ENDPOINT is required when using Azure provider")
        elif cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq provider")
        elif cls.LLM_PROVIDER == "deepseek" and not cls.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is required when using DeepSeek provider")
        # Ollama doesn't require API key (local)

        return True
