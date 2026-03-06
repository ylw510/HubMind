"""
Project Discovery subgraph: parse requirement -> search (trending/search) -> return payload.
"""
from typing import Any, Dict, Optional
import re

from .state import AgentState


def _extract_language(text: str) -> Optional[str]:
    lang_map = {
        "python": "python", "java": "java", "javascript": "javascript",
        "typescript": "typescript", "go": "go", "rust": "rust", "cpp": "cpp", "c++": "cpp",
    }
    lowered = text.lower()
    for key, lang in lang_map.items():
        if key in lowered:
            return lang
    return None


def project_discovery_node(
    state: AgentState,
    *,
    get_trending_tool,
) -> AgentState:
    """
    Single node: use message to drive trending/search, produce payload for render.
    get_trending_tool: callable that returns GitHubTrendingTool instance (or we pass tool in config).
    """
    message = state.get("message") or ""
    try:
        tool = get_trending_tool()
        language = _extract_language(message)
        since = "daily"
        if any(k in message for k in ["本周", "一周", "weekly", "这周"]):
            since = "weekly"
        if any(k in message for k in ["本月", "一月", "monthly", "这月"]):
            since = "monthly"
        limit = 10
        m = re.search(r"(\d+)\s*个(项目|repo)", message)
        if m:
            try:
                limit = max(3, min(30, int(m.group(1))))
            except ValueError:
                pass

        repos = tool.get_trending_repos(language=language, since=since, limit=limit)
        summary = tool.get_trending_summary(
            repos, language=language, since=since, use_llm=True
        )
        items = [
            {
                "name": r.get("name") or r.get("full_name"),
                "description": r.get("description") or "",
                "stars": r.get("stars") or r.get("stargazers_count"),
                "language": r.get("language"),
                "url": r.get("url"),
            }
            for r in repos
        ]
        payload: Dict[str, Any] = {
            "type": "project_discovery",
            "title": "🔍 项目发现结果",
            "summary": summary,
            "items": items,
        }
        return {**state, "payload": payload}
    except Exception as e:
        return {**state, "payload": {"type": "error", "message": str(e)}}
