"""
LLM Factory - Support for multiple LLM providers using LangChain Model I/O

This module leverages LangChain's Model I/O abstraction to provide a unified
interface for different LLM providers. All LLMs implement BaseChatModel,
ensuring consistent behavior across providers.
"""
import os
from typing import Optional, Any, Dict
from langchain_core.language_models import BaseChatModel
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class LLMFactory:
    """
    Factory class for creating LLM instances from different providers

    Uses LangChain's Model I/O abstraction (BaseChatModel) to provide
    a unified interface. All LLMs are interchangeable through this interface.

    Example:
        # Same code works with any provider
        llm = LLMFactory.create_llm(provider="openai")
        llm = LLMFactory.create_llm(provider="anthropic")
        llm = LLMFactory.create_llm(provider="ollama")

        # All return BaseChatModel, can be used identically
        response = llm.invoke("Hello")
    """

    # Provider configuration mapping
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "deepseek": {
            "default_model": "deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "package": "langchain-openai",  # Uses OpenAI-compatible API
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
            "api_key_env": None,  # No API key needed
            "package": "langchain-ollama",
        },
        "groq": {
            "default_model": "mixtral-8x7b-32768",
            "api_key_env": "GROQ_API_KEY",
            "package": "langchain-groq",
        },
    }

    @staticmethod
    def create_llm(
        provider: str = "openai",
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance using LangChain Model I/O unified interface

        All providers return BaseChatModel, ensuring consistent behavior.
        The same code works with any provider - just change the provider parameter.

        Supported providers:
        - deepseek: DeepSeek models (default, OpenAI-compatible)
        - openai: OpenAI models (GPT-4, GPT-3.5, etc.)
        - anthropic: Anthropic Claude models
        - google: Google Gemini models
        - azure: Azure OpenAI
        - ollama: Local Ollama models
        - groq: Groq models

        Args:
            provider: LLM provider name
            model_name: Model name (optional, uses provider default if not provided)
            temperature: Model temperature
            **kwargs: Additional provider-specific arguments

        Returns:
            BaseChatModel instance (LangChain Model I/O interface)

        Example:
            # Works with any provider - same interface
            llm1 = LLMFactory.create_llm(provider="openai")
            llm2 = LLMFactory.create_llm(provider="anthropic")
            llm3 = LLMFactory.create_llm(provider="ollama")

            # All can be used identically
            response1 = llm1.invoke("Hello")
            response2 = llm2.invoke("Hello")
            response3 = llm3.invoke("Hello")
        """
        provider = provider.lower()

        if provider not in LLMFactory.PROVIDER_CONFIGS:
            supported = ", ".join(LLMFactory.PROVIDER_CONFIGS.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {supported}"
            )

        # Use default model if not specified
        if not model_name:
            model_name = LLMFactory.PROVIDER_CONFIGS[provider]["default_model"]

        # Route to provider-specific creation method
        if provider == "deepseek":
            return LLMFactory._create_deepseek(model_name, temperature, **kwargs)
        elif provider == "openai":
            return LLMFactory._create_openai(model_name, temperature, **kwargs)
        elif provider == "anthropic":
            return LLMFactory._create_anthropic(model_name, temperature, **kwargs)
        elif provider == "google":
            return LLMFactory._create_google(model_name, temperature, **kwargs)
        elif provider == "azure":
            return LLMFactory._create_azure(model_name, temperature, **kwargs)
        elif provider == "ollama":
            return LLMFactory._create_ollama(model_name, temperature, **kwargs)
        elif provider == "groq":
            return LLMFactory._create_groq(model_name, temperature, **kwargs)

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
