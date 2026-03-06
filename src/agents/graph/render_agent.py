"""
Render Agent: structured payload -> Markdown (tables, links).
"""
from typing import Any, Dict, List

from .state import AgentState


def _truncate(text: str, max_len: int) -> str:
    """Safely truncate text for table cells and add ellipsis when needed."""
    if text is None:
        return "-"
    s = str(text).replace("|", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def render_payload_to_markdown(payload: Dict[str, Any]) -> str:
    """
    Convert structured payload to user-facing Markdown.
    Supports: project_discovery, issue_list, pr_list, pr_analysis, error.
    """
    if not payload:
        return ""
    ptype = payload.get("type") or "unknown"

    if ptype == "project_discovery":
        return _render_project_discovery(payload)
    if ptype == "issue_list":
        return _render_issue_list(payload)
    if ptype == "pr_list":
        return _render_pr_list(payload)
    if ptype == "pr_analysis":
        return _render_pr_analysis(payload)
    if ptype == "error":
        return _render_error(payload)
    # generic: if payload has "markdown" key, use it
    if "markdown" in payload:
        return payload["markdown"]
    return f"```json\n{payload}\n```"


def _render_project_discovery(p: Dict[str, Any]) -> str:
    title = p.get("title") or "🔍 项目发现结果"
    summary = p.get("summary") or ""
    items = p.get("items") or []
    lines = [f"## {title}\n", summary] if summary else [f"## {title}\n"]
    if not items:
        return "\n".join(lines)
    lines.append("\n| 项目 | 描述 | Stars | 语言 | 链接 |")
    lines.append("|------|------|-------|------|------|")
    for r in items[:20]:
        name = r.get("name") or r.get("full_name") or "-"
        desc = _truncate(r.get("description") or "-", 60)
        stars = r.get("stars", r.get("stargazers_count", "-"))
        lang = r.get("language") or "-"
        url = r.get("url") or "#"
        lines.append(f"| {name} | {desc} | {stars} | {lang} | [打开]({url}) |")
    return "\n".join(lines)


def _render_issue_list(p: Dict[str, Any]) -> str:
    repo = p.get("repo") or ""
    state = p.get("state") or "open"
    scope = p.get("scope") or ""
    items = p.get("items") or []
    title = f"📌 仓库 `{repo}` 的 {state} Issues"
    if scope == "self":
        title = "🧩 自仓 Issue\n\n" + title
    lines = [f"## {title}\n"]
    if not items:
        lines.append("暂无匹配的 Issue。")
        return "\n".join(lines)
    lines.append("| # | 标题 | 状态 | 作者 | 标签 | 链接 |")
    lines.append("|---|------|------|------|------|------|")
    for i in items[:30]:
        num = i.get("number") or "-"
        title_text = _truncate(i.get("title") or "-", 50)
        state_val = i.get("state") or "-"
        author_raw = i.get("author") or i.get("user") or "-"
        if isinstance(author_raw, dict):
            author = author_raw.get("login") or author_raw.get("name") or "-"
        else:
            author = str(author_raw)
        labels_raw = i.get("labels") or []
        label_names: List[str] = []
        for lab in labels_raw[:3]:
            if isinstance(lab, dict):
                name = lab.get("name") or ""
            else:
                name = str(lab)
            if name:
                label_names.append(_truncate(name, 20))
        labels = ", ".join(label_names)
        url = i.get("url") or "#"
        lines.append(f"| #{num} | {title_text} | {state_val} | {author} | {labels} | [链接]({url}) |")
    return "\n".join(lines)


def _render_pr_list(p: Dict[str, Any]) -> str:
    repo = p.get("repo") or ""
    title = p.get("title") or "📬 PR 列表"
    items = p.get("items") or []
    lines = [f"## {title} · `{repo}`\n"]
    if not items:
        lines.append("暂无匹配的 PR。")
        return "\n".join(lines)
    lines.append("| # | 标题 | 作者 | 状态 | 评论 | 价值分 | 链接 |")
    lines.append("|---|------|------|------|------|--------|------|")
    for i in items[:30]:
        num = i.get("number") or "-"
        title_text = _truncate(i.get("title") or "-", 45)
        author_raw = i.get("author") or "-"
        if isinstance(author_raw, dict):
            author = author_raw.get("login") or author_raw.get("name") or "-"
        else:
            author = str(author_raw)
        state_val = i.get("state") or "-"
        comments = i.get("comments") or 0
        score = i.get("value_score", "-")
        url = i.get("url") or "#"
        lines.append(f"| #{num} | {title_text} | {author} | {state_val} | {comments} | {score} | [链接]({url}) |")
    return "\n".join(lines)


def _render_pr_analysis(p: Dict[str, Any]) -> str:
    lines = ["## 🔍 PR 分析\n"]
    lines.append(f"- **仓库**: `{p.get('repo', '')}`")
    lines.append(f"- **PR**: #{p.get('number')} {p.get('title', '')}")
    author_raw = p.get("author") or "-"
    if isinstance(author_raw, dict):
        author = author_raw.get("login") or author_raw.get("name") or "-"
    else:
        author = str(author_raw)
    lines.append(f"- 作者: {author} | 状态: {p.get('state')} | 价值分: {p.get('value_score')}")
    lines.append(f"- 改动: +{p.get('additions')} / -{p.get('deletions')} | 文件数: {p.get('files_changed')}")
    lines.append(f"- [打开 PR]({p.get('url', '#')})\n")
    if p.get("summary"):
        lines.append("### 摘要\n" + p["summary"])
    if p.get("risks"):
        lines.append("\n### 风险点\n" + p["risks"])
    return "\n".join(lines)


def _render_error(p: Dict[str, Any]) -> str:
    msg = p.get("message") or "未知错误"
    return f"⚠️ {msg}"


def render_node(state: AgentState) -> AgentState:
    """
    LangGraph node: take state["payload"] or state["final_message"], write state["response"].
    """
    if state.get("final_message"):
        return {**state, "response": state["final_message"]}
    payload = state.get("payload") or {}
    response = render_payload_to_markdown(payload)
    return {**state, "response": response or "暂无内容。"}
