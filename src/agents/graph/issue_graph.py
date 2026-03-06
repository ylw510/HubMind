"""
Issue subgraph: self vs other scope, list/create issues -> payload.
"""
import re
from typing import Any, Dict

from .state import AgentState


def _extract_repo(text: str) -> str | None:
    m = re.search(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", text)
    return m.group(1) if m else None


def issue_node(
    state: AgentState,
    *,
    get_issue_tool,
) -> AgentState:
    """
    Produce issue_list payload (or error). Scope from state["intent_detail"] (self/other).
    """
    message = state.get("message") or ""
    scope = state.get("intent_detail") or "other"
    try:
        tool = get_issue_tool()
        repo = _extract_repo(message)
        if not repo:
            return {
                **state,
                "payload": {
                    "type": "error",
                    "message": "未识别到仓库名，请提供 owner/repo 格式，例如 microsoft/vscode。",
                },
            }
        state_issue = "closed" if ("关闭" in message or "closed" in message.lower()) else "open"
        limit = 25
        issues = tool.get_issues(repo, state=state_issue, limit=limit)
        if not issues or (isinstance(issues, list) and issues and issues[0].get("error")):
            return {
                **state,
                "payload": {
                    "type": "issue_list",
                    "repo": repo,
                    "state": state_issue,
                    "scope": scope,
                    "items": [],
                },
            }
        items = [
            {
                "number": i.get("number"),
                "title": i.get("title"),
                "state": i.get("state"),
                "author": i.get("author"),
                "labels": i.get("labels") or [],
                "url": i.get("url"),
            }
            for i in issues
        ]
        payload: Dict[str, Any] = {
            "type": "issue_list",
            "repo": repo,
            "state": state_issue,
            "scope": scope,
            "items": items,
        }
        return {**state, "payload": payload}
    except Exception as e:
        return {**state, "payload": {"type": "error", "message": str(e)}}
