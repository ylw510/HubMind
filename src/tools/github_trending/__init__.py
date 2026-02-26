"""
GitHub Trending：抓取 https://github.com/trending -> 数据提取 -> LangChain Agent -> AI 分析总结。

- scraper: 请求并解析 trending 页面 HTML
- analyzer: 基于 LLM 的总结
- GitHubTrendingTool: 对外工具入口（抓取 + 回退 API + 总结）
"""
from .tool import GitHubTrendingTool
from . import scraper
from . import analyzer

__all__ = ["GitHubTrendingTool", "scraper", "analyzer"]
