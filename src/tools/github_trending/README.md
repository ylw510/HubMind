# GitHub Trending 模块

数据流与职责划分：

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐
│  GitHub Trending│ -> │  抓取模块     │ -> │  LangChain Agent│ -> │  AI 分析总结 │
│  页面 (HTML)    │    │ (数据提取)    │    │  (状态管理)     │    │  (LLM调用)   │
└─────────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘
        │                      │                      │                      │
        │                      │                      │                      │
        v                      v                      v                      v
  https://github.com/    scraper.py            tool.py / Agent         analyzer.py
  trending?language=     fetch + parse         get_trending_repos      summarize_with_llm
  python&since=daily     -> List[Dict]          get_trending_summary
```

- **scraper**：请求 trending 页、解析 `article.Box-row`，输出结构化列表；失败时由 tool 回退到 Search API。
- **tool (GitHubTrendingTool)**：对外接口；组合抓取 + 回退 + 调用 analyzer 做总结。
- **analyzer**：用 LLM 对列表做 2～4 句趋势概括与亮点；失败时退回纯文本列表。
