"""
LangGraph multi-agent orchestration for HubMind.

- state: shared AgentState
- nodes: router, render, and subgraph entry nodes
- project_discovery_graph: 项目发现子图
- issue_graph: Issue 管理子图（自仓/他仓）
- pr_analysis_graph: PR 分析子图
- supervisor_graph: 主图（路由 + 子图 + 渲染）
"""

from .state import AgentState
from .supervisor_graph import create_supervisor_graph

__all__ = ["AgentState", "create_supervisor_graph"]
