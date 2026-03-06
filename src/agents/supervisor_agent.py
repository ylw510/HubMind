"""
Multi-agent Supervisor for HubMind.

Uses LangGraph for orchestration:
- Router -> project_discovery | issue | pr_analysis | fallback -> render -> response
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from config import Config
from src.utils.llm_factory import LLMFactory
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.agents.hubmind_agent import HubMindAgent
from src.agents.graph import create_supervisor_graph


class SupervisorAgent:
    """
    顶层 Supervisor，使用 LangGraph 编排：
    路由 -> 项目发现 | Issue | PR 分析 | 兜底 Agent -> 渲染 -> 响应
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        github_token: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: Optional[str] = None,
    ) -> None:
        use_overrides = bool(github_token and llm_api_key)
        if not use_overrides:
            Config.validate()

        provider = (provider or Config.LLM_PROVIDER).lower()
        model_name = model_name or Config.LLM_MODEL or llm_model or None

        llm_kwargs: Dict[str, Any] = {}
        if llm_api_key:
            llm_kwargs["api_key"] = llm_api_key
        if provider == "openai_compatible" and llm_base_url:
            llm_kwargs["base_url"] = llm_base_url.rstrip("/")
        if provider == "openai_compatible" and (llm_model or model_name):
            llm_kwargs["model"] = llm_model or model_name
            model_name = llm_model or model_name

        self.router_llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            **llm_kwargs,
        )

        self.trending_tool = GitHubTrendingTool(
            github_token=github_token,
            llm_provider=provider,
            llm_api_key=llm_api_key,
        )
        self.issue_tool = GitHubIssueTool(github_token=github_token)
        self.pr_tool = GitHubPRTool(github_token=github_token)
        self.fallback_agent = HubMindAgent(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            github_token=github_token,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
        )

        self.graph = create_supervisor_graph(
            get_trending_tool=lambda: self.trending_tool,
            get_issue_tool=lambda: self.issue_tool,
            get_pr_tool=lambda: self.pr_tool,
            get_fallback_agent=lambda: self.fallback_agent,
            get_llm=lambda: self.router_llm,
        )

    def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Invoke LangGraph and return final response."""
        chat_history = chat_history or []
        try:
            result = self.graph.invoke(
                {"message": message, "chat_history": chat_history},
                config={"configurable": {"thread_id": "default"}},
            )
            return result.get("response") or result.get("final_message") or "暂无回复。"
        except (BrokenPipeError, ConnectionError, OSError):
            return "连接中断，请刷新页面重试。"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"处理请求时出错: {str(e)}。请检查配置是否正确。"

