"""
Supervisor Graph: LangGraph main graph.
Router -> project_discovery | issue | pr_analysis | fallback -> render -> END.
"""
from typing import Any, Callable, Dict, List, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .render_agent import render_node
from .project_discovery_graph import project_discovery_node
from .issue_graph import issue_node
from .pr_analysis_graph import pr_analysis_node


# ---------- Router ----------
def _heuristic_intent(message: str) -> tuple[str, Optional[str]]:
    lowered = message.lower()
    if any(k in lowered for k in ["trending", "热门", "最火", "趋势", "发现项目", "推荐项目", "推荐.*项目", "开源项目", "ai领域"]):
        return "project_discovery", None
    if any(k in lowered for k in ["issue", "问题", "bug", "工单", "提issue", "接issue"]):
        scope = "self" if ("我的" in message or "自仓" in message or "自己仓库" in message) else "other"
        return "issues", scope
    if any(k in lowered for k in ["pr", "pull request", "合并请求", "review", "分析.*pr", "内存.*pr"]):
        return "pr_analysis", None
    return "general", None


def router_node(state: AgentState) -> AgentState:
    """Set intent and intent_detail from message."""
    message = state.get("message") or ""
    intent, detail = _heuristic_intent(message)
    return {**state, "intent": intent, "intent_detail": detail}


def _route_after_router(state: AgentState) -> str:
    """Conditional edge: which node to run next."""
    return state.get("intent") or "general"


# ---------- Fallback: call HubMindAgent.chat ----------
def make_fallback_node(get_fallback_agent: Callable):
    def fallback_node(state: AgentState) -> AgentState:
        agent = get_fallback_agent()
        message = state.get("message") or ""
        chat_history = state.get("chat_history") or []
        try:
            final_message = agent.chat(message, chat_history)
        except Exception as e:
            final_message = f"处理时出错: {str(e)}"
        return {**state, "final_message": final_message}
    return fallback_node


# ---------- Graph builder ----------
def create_supervisor_graph(
    *,
    get_trending_tool: Callable,
    get_issue_tool: Callable,
    get_pr_tool: Callable,
    get_fallback_agent: Callable,
    get_llm: Optional[Callable] = None,
) -> Any:
    """
    Build the compiled LangGraph.

    Dependencies are injected as get_* callables so that the graph can be
    created once and reused with per-request user settings (e.g. tokens) via config.
    """
    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node(
        "project_discovery",
        lambda s: project_discovery_node(s, get_trending_tool=get_trending_tool),
    )
    builder.add_node(
        "issue",
        lambda s: issue_node(s, get_issue_tool=get_issue_tool),
    )
    builder.add_node(
        "pr_analysis",
        lambda s: pr_analysis_node(
            s,
            get_pr_tool=get_pr_tool,
            get_llm=get_llm or (lambda: None),
        ),
    )
    builder.add_node("fallback", make_fallback_node(get_fallback_agent))
    builder.add_node("render", render_node)

    builder.set_entry_point("router")
    builder.add_conditional_edges("router", _route_after_router, {
        "project_discovery": "project_discovery",
        "issues": "issue",
        "pr_analysis": "pr_analysis",
        "general": "fallback",
    })
    builder.add_edge("project_discovery", "render")
    builder.add_edge("issue", "render")
    builder.add_edge("pr_analysis", "render")
    builder.add_edge("fallback", "render")
    builder.add_edge("render", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
