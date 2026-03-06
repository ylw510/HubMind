"""
PR Analysis subgraph: parse query (repo, days, topic, top_n) -> fetch -> filter by topic -> rank -> payload.
"""
import re
from typing import Any, Dict, List, Optional

from .state import AgentState


def _extract_repo(text: str) -> Optional[str]:
    m = re.search(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", text)
    return m.group(1) if m else None


def _extract_days(text: str) -> int:
    if any(k in text for k in ["一周", "7天", "最近一周", "week", "7 days"]):
        return 7
    if any(k in text for k in ["两周", "14天"]):
        return 14
    m = re.search(r"(\d+)\s*天", text)
    if m:
        try:
            return max(1, min(90, int(m.group(1))))
        except ValueError:
            pass
    return 7


def _extract_topic_keywords(text: str) -> List[str]:
    """Simple keyword extraction for topic filter (e.g. 内存 -> memory)."""
    keywords = []
    text_lower = text.lower()
    # Map common Chinese to English for matching PR title/body
    topic_map = [
        ("内存", "memory"), ("memory", "memory"),
        ("性能", "performance"), ("performance", "performance"),
        ("bug", "bug"), ("修复", "fix"), ("fix", "fix"),
        ("安全", "security"), ("security", "security"),
    ]
    for zh_en, en in topic_map:
        if zh_en in text or en in text_lower:
            keywords.append(en)
    # Fallback: take first few meaningful words from Chinese
    if not keywords:
        for w in ["内存", "性能", "bug", "修复", "优化", "提升"]:
            if w in text:
                keywords.append(w)
    return keywords[:5]


def _extract_top_n(text: str, default: int = 10) -> int:
    m = re.search(r"(\d+)\s*个?\s*pr", text, re.IGNORECASE)
    if m:
        try:
            return max(1, min(30, int(m.group(1))))
        except ValueError:
            pass
    m = re.search(r"最有价值的\s*(\d+)\s*个", text)
    if m:
        try:
            return max(1, min(30, int(m.group(1))))
        except ValueError:
            pass
    return default


def pr_analysis_node(
    state: AgentState,
    *,
    get_pr_tool,
    get_llm,
) -> AgentState:
    """
    Fetch PRs in time range, optionally filter by topic with LLM, rank by value, return payload.
    """
    message = state.get("message") or ""
    try:
        pr_tool = get_pr_tool()
        repo = _extract_repo(message)
        if not repo:
            return {
                **state,
                "payload": {
                    "type": "error",
                    "message": "未识别到仓库名，请提供 owner/repo，例如 ClickHouse/ClickHouse。",
                },
            }

        pr_number = None
        m = re.search(r"#(\d+)", message)
        if m:
            pr_number = int(m.group(1))
        if not m:
            m = re.search(r"\bpr\s*(\d+)\b", message, re.IGNORECASE)
            if m:
                pr_number = int(m.group(1))

        if pr_number is not None:
            analysis = pr_tool.analyze_pr(repo, pr_number)
            if isinstance(analysis, dict) and analysis.get("error"):
                return {
                    **state,
                    "payload": {"type": "error", "message": analysis["error"]},
                }
            payload: Dict[str, Any] = {
                "type": "pr_analysis",
                "repo": repo,
                "number": analysis.get("number"),
                "title": analysis.get("title"),
                "author": analysis.get("author"),
                "state": analysis.get("state"),
                "value_score": analysis.get("value_score"),
                "additions": analysis.get("additions"),
                "deletions": analysis.get("deletions"),
                "files_changed": analysis.get("files_changed"),
                "url": analysis.get("url"),
                "summary": analysis.get("summary", ""),
                "risks": analysis.get("risks", ""),
            }
            return {**state, "payload": payload}

        days = _extract_days(message)
        top_n = _extract_top_n(message)
        topic_kw = _extract_topic_keywords(message)

        prs = pr_tool.get_prs_since_days(repo, days=days, limit=50)
        if not prs or (prs and prs[0].get("error")):
            return {
                **state,
                "payload": {
                    "type": "pr_list",
                    "repo": repo,
                    "title": "📬 PR 列表",
                    "items": [],
                },
            }

        if topic_kw:
            filtered = []
            for pr in prs:
                title = (pr.get("title") or "").lower()
                body = (pr.get("body") or "").lower()
                combined = title + " " + body
                if any(kw in combined for kw in topic_kw):
                    filtered.append(pr)
            prs = filtered[: top_n * 2]

        prs_sorted = sorted(
            prs,
            key=lambda x: x.get("value_score") or 0,
            reverse=True,
        )[:top_n]

        items = [
            {
                "number": p.get("number"),
                "title": p.get("title"),
                "author": p.get("author"),
                "state": p.get("state"),
                "comments": p.get("comments"),
                "value_score": p.get("value_score"),
                "url": p.get("url"),
            }
            for p in prs_sorted
        ]
        title = f"⭐ 最近{days}天最有价值的 {len(items)} 个 PR"
        if topic_kw:
            title += f"（主题: {'/'.join(topic_kw)}）"
        return {
            **state,
            "payload": {
                "type": "pr_list",
                "repo": repo,
                "title": title,
                "items": items,
            },
        }
    except Exception as e:
        return {**state, "payload": {"type": "error", "message": str(e)}}
