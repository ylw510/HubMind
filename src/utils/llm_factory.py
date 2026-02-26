"""
LLM Factory - Support for multiple LLM providers using LangChain Model I/O

This module leverages LangChain's Model I/O abstraction to provide a unified
interface for different LLM providers. All LLMs implement BaseChatModel,
ensuring consistent behavior across providers.

Supports:
- Built-in providers via registry (deepseek, openai, anthropic, google, azure, ollama, groq).
- openai_compatible: any OpenAI-compatible API (base_url + api_key + model_name).
- Custom providers via LLMFactory.register(name, creator_fn).
"""
import os
from typing import Optional, Any, Dict, Callable
from langchain_core.language_models import BaseChatModel
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config

# Type for provider creator: (model_name, temperature, **kwargs) -> BaseChatModel
_CreatorFn = Callable[..., BaseChatModel]


class LLMFactory:
    """
    Factory class for creating LLM instances from different providers

    Uses a registry: built-in providers are registered at import time.
    Use openai_compatible for any OpenAI-compatible API, or register()
    to add custom providers without editing this file.

    Example:
        llm = LLMFactory.create_llm(provider="openai")
        llm = LLMFactory.create_llm(
            provider="openai_compatible",
            model_name="my-model",
            base_url="https://api.example.com/v1",
            api_key="sk-...",
        )
    """

    # Provider configuration (default models, env hints; registry holds creators)
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "deepseek": {
            "default_model": "deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "package": "langchain-openai",
        },
        "openai": {
            "default_model": "gpt-4-turbo-preview",
            "api_key_env": "OPENAI_API_KEY",
            "package": "langchain-openai",
        },
        "anthropic": {
            "default_model": "claude-3-opus-20240229",
            "api_key_env": "ANTHROPIC_API_KEY",
            "package": "langchain-anthropic",
        },
        "google": {
            "default_model": "gemini-pro",
            "api_key_env": "GOOGLE_API_KEY",
            "package": "langchain-google-genai",
        },
        "azure": {
            "default_model": "gpt-4",
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "package": "langchain-openai",
        },
        "ollama": {
            "default_model": "llama2",
            "api_key_env": None,
            "package": "langchain-ollama",
        },
        "groq": {
            "default_model": "mixtral-8x7b-32768",
            "api_key_env": "GROQ_API_KEY",
            "package": "langchain-groq",
        },
        "openai_compatible": {
            "default_model": "",  # caller must pass model_name or kwargs["model"]
            "api_key_env": None,
            "package": "langchain-openai",
        },
    }

    # Registry: provider_name -> creator(model_name, temperature, **kwargs) -> BaseChatModel
    _CREATORS: Dict[str, _CreatorFn] = {}

    @classmethod
    def register(cls, name: str, creator: _CreatorFn) -> None:
        """Register a provider. name is case-insensitive (stored lower)."""
        cls._CREATORS[name.lower()] = creator

    @classmethod
    def create_llm(
        cls,
        provider: str = "openai",
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance using LangChain Model I/O unified interface.

        Providers are resolved from the registry. Built-in: deepseek, openai,
        anthropic, google, azure, ollama, groq. Use provider="openai_compatible"
        for any OpenAI-compatible API (pass base_url, api_key, model_name in kwargs).
        Add custom providers with LLMFactory.register(name, creator_fn).

        Args:
            provider: LLM provider name (case-insensitive)
            model_name: Model name (optional; uses provider default when available)
            temperature: Model temperature
            **kwargs: Provider-specific (e.g. api_key, base_url for openai_compatible)

        Returns:
            BaseChatModel instance
        """
        provider = provider.lower()

        if provider not in cls._CREATORS:
            supported = ", ".join(sorted(cls._CREATORS.keys()))
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Registered providers: {supported}. "
                "Use provider='openai_compatible' with base_url, api_key, model_name for custom APIs."
            )

        # Default model from config when not specified
        if not model_name and provider in cls.PROVIDER_CONFIGS:
            model_name = cls.PROVIDER_CONFIGS[provider].get("default_model") or None

        creator = cls._CREATORS[provider]
        return creator(model_name, temperature, **kwargs)

    @staticmethod
    def _create_deepseek(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create DeepSeek LLM (OpenAI-compatible API)"""
        from langchain_openai import ChatOpenAI

        api_key = kwargs.get("api_key") or Config.DEEPSEEK_API_KEY
        base_url = kwargs.get("base_url") or Config.DEEPSEEK_BASE_URL

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek provider")

        return ChatOpenAI(
            model=model_name or "deepseek-chat",
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            **{k: v for k, v in kwargs.items() if k not in ["api_key", "base_url"]}
        )

    @staticmethod
    def _create_openai(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create OpenAI LLM"""
        from langchain_openai import ChatOpenAI

        api_key = kwargs.get("api_key") or Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        return ChatOpenAI(
            model=model_name or "gpt-4-turbo-preview",
            temperature=temperature,
            api_key=api_key,
            **{k: v for k, v in kwargs.items() if k != "api_key"}
        )

    @staticmethod
    def _create_anthropic(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create Anthropic Claude LLM"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is not installed. "
                "Install it with: pip install langchain-anthropic"
            )

        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

        return ChatAnthropic(
            model=model_name or "claude-3-opus-20240229",
            temperature=temperature,
            api_key=api_key,
            **{k: v for k, v in kwargs.items() if k != "api_key"}
        )

    @staticmethod
    def _create_google(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create Google Gemini LLM"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai is not installed. "
                "Install it with: pip install langchain-google-genai"
            )

        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Google provider")

        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-pro",
            temperature=temperature,
            google_api_key=api_key,
            **{k: v for k, v in kwargs.items() if k != "api_key"}
        )

    @staticmethod
    def _create_azure(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create Azure OpenAI LLM"""
        from langchain_openai import AzureChatOpenAI

        api_key = kwargs.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = kwargs.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT")

        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required for Azure provider")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure provider")

        return AzureChatOpenAI(
            model=model_name or "gpt-4",
            temperature=temperature,
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=kwargs.get("api_version", "2024-02-15-preview"),
            **{k: v for k, v in kwargs.items() if k not in ["api_key", "endpoint", "api_version"]}
        )

    @staticmethod
    def _create_ollama(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create Ollama LLM (local models)"""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is not installed. "
                "Install it with: pip install langchain-ollama"
            )

        base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        return ChatOllama(
            model=model_name or "llama2",
            temperature=temperature,
            base_url=base_url,
            **{k: v for k, v in kwargs.items() if k != "base_url"}
        )

    @staticmethod
    def _create_groq(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """Create Groq LLM"""
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "langchain-groq is not installed. "
                "Install it with: pip install langchain-groq"
            )

        api_key = kwargs.get("api_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for Groq provider")

        return ChatGroq(
            model=model_name or "mixtral-8x7b-32768",
            temperature=temperature,
            groq_api_key=api_key,
            **{k: v for k, v in kwargs.items() if k != "api_key"}
        )

    @staticmethod
    def _create_openai_compatible(
        model_name: Optional[str],
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """
        Create LLM for any OpenAI-compatible API (e.g. Moonshot, 智谱, OpenRouter).
        Requires base_url, api_key, and model (or model_name) in kwargs or env.
        """
        from langchain_openai import ChatOpenAI

        base_url = kwargs.get("base_url") or os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        model = (
            model_name
            or kwargs.get("model")
            or kwargs.get("model_name")
        )

        if not base_url:
            raise ValueError(
                "base_url is required for openai_compatible provider "
                "(pass in kwargs or set OPENAI_COMPATIBLE_BASE_URL)"
            )
        if not api_key:
            raise ValueError(
                "api_key is required for openai_compatible provider "
                "(pass in kwargs or set OPENAI_COMPATIBLE_API_KEY)"
            )
        if not model:
            raise ValueError(
                "model_name (or model) is required for openai_compatible provider"
            )

        passthrough = {k: v for k, v in kwargs.items() if k not in ("base_url", "api_key", "model", "model_name")}
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            **passthrough
        )


def _register_builtins() -> None:
    """Register all built-in providers so create_llm() resolves by name."""
    LLMFactory.register("deepseek", LLMFactory._create_deepseek)
    LLMFactory.register("openai", LLMFactory._create_openai)
    LLMFactory.register("anthropic", LLMFactory._create_anthropic)
    LLMFactory.register("google", LLMFactory._create_google)
    LLMFactory.register("azure", LLMFactory._create_azure)
    LLMFactory.register("ollama", LLMFactory._create_ollama)
    LLMFactory.register("groq", LLMFactory._create_groq)
    LLMFactory.register("openai_compatible", LLMFactory._create_openai_compatible)


_register_builtins()
