# HubMind 多智能体架构（LangGraph）

## 概览

```
┌─────────────────────────────────────────────────────────────┐
│                       用户对话界面                            │
│              (支持 Markdown / 链接 / 表格渲染)                 │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Supervisor (LangGraph)                     │
│  • 意图识别 (router_node)                                    │
│  • 任务路由 (conditional_edges)                              │
│  • 结果整合 (render_node)                                    │
└───┬──────────┬──────────┬──────────┬────────────────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 项目发现 │ │ Issue   │ │ PR 分析 │ │ Fallback│
│ (子图)   │ │ (子图)  │ │ (子图)  │ │(HubMind)│
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                     外部工具 / API 层                         │
│  GitHub API │ Trending 抓取 │ PR/Issue 工具 │ LLM           │
└─────────────────────────────────────────────────────────────┘
```

## 1. 对话层

- 前端：单页对话 + 推荐问题 / TRENDING 看板，Markdown（含链接、表格）渲染。
- 后端入口：`POST /api/chat`，请求体 `{ message, chat_history }`，返回 `{ response, chat_history }`。

## 2. 编排层（LangGraph）

- **状态**：`AgentState`（`src/agents/graph/state.py`）
  - 输入：`message`, `chat_history`
  - 路由：`intent`（project_discovery | issues | pr_analysis | general）, `intent_detail`（如 issue 的 self/other）
  - 子图输出：`payload`（结构化，供渲染）或 `final_message`（兜底直接文案）
  - 最终输出：`response`（Markdown 字符串）

- **主图**：`create_supervisor_graph`（`src/agents/graph/supervisor_graph.py`）
  - **router_node**：启发式意图识别（关键词：热门/最火/趋势/issue/pr 等），写 `intent` / `intent_detail`。
  - **conditional_edges**：根据 `intent` 进入 project_discovery / issue / pr_analysis / fallback 之一。
  - **project_discovery_node**：解析时间范围与语言 → 调用 `GitHubTrendingTool` → 返回 `payload.type=project_discovery`。
  - **issue_node**：解析 repo、state → 调用 `GitHubIssueTool.get_issues` → 返回 `payload.type=issue_list`（含 scope=self/other）。
  - **pr_analysis_node**：解析 repo、时间范围、主题关键词、top_n；单 PR 时走 `analyze_pr`，否则 `get_prs_since_days` + 主题过滤 + 按价值排序 → `payload.type=pr_list` 或 `pr_analysis`。
  - **fallback_node**：调用 `HubMindAgent.chat(message, chat_history)`，结果写入 `final_message`。
  - **render_node**：根据 `payload.type` 或 `final_message` 生成 Markdown（表格、链接），写入 `response`。
  - 所有分支汇聚到 `render` → END。

## 3. 能力与需求对应

| 需求 | 意图 | 子图 / 节点 | 工具 / 说明 |
|------|------|-------------|-------------|
| 项目发现 / 推荐 | project_discovery | project_discovery_node | GitHubTrendingTool（抓取 + LLM 总结） |
| 自仓 Issue 管理 | issues (detail=self) | issue_node | GitHubIssueTool.get_issues |
| 他仓 Issue / 接 issue | issues (detail=other) | issue_node | 同上，payload 中 scope=other |
| PR 列表 / 按主题筛选 | pr_analysis | pr_analysis_node | GitHubPRTool.get_prs_since_days + 关键词过滤 |
| 单 PR 深度分析 | pr_analysis（带 #123） | pr_analysis_node | GitHubPRTool.analyze_pr |
| 其他综合对话 | general | fallback_node | HubMindAgent（LangChain Tools） |
| 结果展示 | - | render_node | payload → Markdown 表格/链接 |

## 4. 渲染能力（RenderAgent）

- 输入：`state.payload`（type + items/repo/...）或 `state.final_message`。
- 输出：`state.response`（Markdown）。
- 支持类型：`project_discovery`（项目表）、`issue_list`（Issue 表）、`pr_list`（PR 表）、`pr_analysis`（单 PR 详情）、`error`（错误提示）。

## 5. 文件结构

```
src/agents/
├── graph/
│   ├── __init__.py          # 导出 AgentState, create_supervisor_graph
│   ├── state.py             # AgentState TypedDict
│   ├── supervisor_graph.py  # 主图：router + 条件边 + 各节点 + render
│   ├── project_discovery_graph.py
│   ├── issue_graph.py
│   ├── pr_analysis_graph.py
│   └── render_agent.py      # payload → Markdown
├── supervisor_agent.py       # 对外接口：构造 tools + 编译 graph，chat() 调用 graph.invoke
└── hubmind_agent.py         # Fallback 通用 Agent（LangChain Tools）
```

## 6. 依赖

- `langgraph>=0.2.0`：主图与条件边。
- `langchain` / `langchain-openai` 等：LLM 与 HubMindAgent。

安装：`pip install -r requirements.txt`（含 langgraph）。后端使用 `backend/venv` 时需在该 venv 内安装。
