"""
Shared state for HubMind LangGraph.
"""
from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """State passed through the supervisor and subgraphs."""

    # Input
    message: str
    chat_history: List[Dict[str, str]]

    # Router
    intent: str  # project_discovery | issue_self | issue_other | pr_analysis | general
    intent_detail: Optional[str]  # e.g. scope for issues

    # Structured payload from subgraphs (for render)
    payload: Dict[str, Any]  # type, items, repo, etc.

    # Direct final message (fallback agent or simple reply)
    final_message: str

    # Output (after render)
    response: str
