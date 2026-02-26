"""
AI 分析总结模块：基于 LLM 对 trending 列表做摘要与洞察。

流程：结构化 repo 列表 -> 本模块 (LLM 调用) -> 自然语言总结
"""
from typing import List, Dict, Optional

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from config import Config
from src.utils.llm_factory import LLMFactory


def format_repos_for_prompt(repos: List[Dict], max_items: int = 20) -> str:
    """将 repo 列表格式化为给 LLM 的上下文文本。"""
    if not repos:
        return "（暂无仓库数据）"
    lines = []
    for i, r in enumerate(repos[:max_items], 1):
        name = r.get("name", "")
        desc = (r.get("description") or "")[:200]
        stars = r.get("stars", 0)
        lang = r.get("language") or "N/A"
        url = r.get("url", "")
        lines.append(f"{i}. **{name}** | ⭐ {stars} | {lang}\n   {desc}\n   {url}")
    return "\n\n".join(lines)


def summarize_with_llm(
    repos: List[Dict],
    language: Optional[str] = None,
    since: str = "daily",
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> str:
    """
    使用 LLM 对 trending 列表做简短总结与洞察。
    若未配置 LLM 或调用失败，返回纯文本列表摘要。
    """
    if not repos:
        return "暂无热门仓库数据。"

    provider = (llm_provider or Config.LLM_PROVIDER).lower()
    llm_kwargs = {}
    if llm_api_key:
        llm_kwargs["api_key"] = llm_api_key

    try:
        llm = LLMFactory.create_llm(provider=provider, temperature=0.3, **llm_kwargs)
    except Exception:
        return _plain_summary(repos)

    context = format_repos_for_prompt(repos)
    lang_hint = f"（编程语言筛选: {language}）" if language else ""
    since_hint = {"daily": "今日", "weekly": "本周", "monthly": "本月"}.get(since, since)

    prompt = f"""你是一个 GitHub 热门项目分析助手。下面是从 GitHub Trending 抓取的 {since_hint} 热门仓库列表{lang_hint}。

请用 2～4 句话概括整体趋势（例如：集中在哪些方向、语言或主题），并可选地指出 1～2 个值得关注的项目及原因。语气简洁、信息量足。

仓库列表：
{context}

请直接给出你的总结，不要复述整份列表。"""

    try:
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        if hasattr(response, "content") and response.content:
            return response.content.strip()
    except Exception:
        pass
    return _plain_summary(repos)


def _plain_summary(repos: List[Dict]) -> str:
    """无 LLM 时的纯文本摘要，与原有 get_trending_summary 行为一致。"""
    if not repos:
        return "No trending repositories found."
    summary = f"共 {len(repos)} 个热门仓库：\n\n"
    for i, repo in enumerate(repos, 1):
        summary += f"{i}. **{repo.get('name', '')}** ({repo.get('stars', 0)} ⭐)\n"
        summary += f"   {repo.get('description') or ''}\n"
        summary += f"   语言: {repo.get('language') or 'N/A'} | 链接: {repo.get('url', '')}\n\n"
    return summary
