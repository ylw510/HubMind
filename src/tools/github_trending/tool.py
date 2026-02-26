"""
GitHub Trending Tool：抓取 + 状态/调用入口 + AI 总结。

整体流程：
  GitHub Trending 页面 (HTML) -> 抓取模块 (scraper) -> 结构化数据
  -> LangChain Agent 通过本 Tool 调用
  -> AI 分析总结 (analyzer，LLM) -> 返回用户
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from github import Github

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config import Config

from . import scraper
from . import analyzer


class GitHubTrendingTool:
    """
    热门仓库工具：优先从 https://github.com/trending 抓取，失败时回退到 Search API；
    总结支持 LLM 分析。
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ):
        token = github_token or Config.GITHUB_TOKEN
        self.github = Github(token) if token else None
        self.llm_provider = llm_provider or Config.LLM_PROVIDER
        self.llm_api_key = llm_api_key

    def get_trending_repos(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10,
    ) -> List[Dict]:
        """
        获取热门仓库：先走页面抓取，无结果时用 GitHub Search API 回退。
        """
        repos = scraper.get_trending_from_page(
            language=language,
            since=since,
            limit=limit,
        )
        if repos:
            return repos
        # 回退：Search API（与原有逻辑一致）
        return self._get_trending_fallback(language=language, since=since, limit=limit)

    def _get_since_date(self, since: str) -> str:
        """since -> 日期字符串，用于 Search API 查询。"""
        today = datetime.now()
        if since == "daily":
            date = today - timedelta(days=1)
        elif since == "weekly":
            date = today - timedelta(days=7)
        elif since == "monthly":
            date = today - timedelta(days=30)
        else:
            date = today - timedelta(days=1)
        return date.strftime("%Y-%m-%d")

    def _get_trending_fallback(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10,
    ) -> List[Dict]:
        """使用 GitHub Search API 按 stars 排序作为 trending 回退。"""
        if not self.github:
            return []
        since_date = self._get_since_date(since)
        query = f"created:>{since_date}"
        if language:
            query += f" language:{language}"
        try:
            repos = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc",
            )
        except Exception:
            return []
        trending_list = []
        for repo in repos[:limit]:
            trending_list.append({
                "name": repo.full_name,
                "description": repo.description or "",
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "url": repo.html_url,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "topics": repo.get_topics(),
                "owner": repo.owner.login,
            })
        return trending_list

    def get_trending_summary(
        self,
        repos: List[Dict],
        language: Optional[str] = None,
        since: str = "daily",
        use_llm: bool = True,
    ) -> str:
        """
        生成热门仓库总结。use_llm=True 时走 LLM 分析，失败则退回纯文本列表。
        """
        if use_llm:
            return analyzer.summarize_with_llm(
                repos,
                language=language,
                since=since,
                llm_provider=self.llm_provider,
                llm_api_key=self.llm_api_key,
            )
        return analyzer._plain_summary(repos)

    def analyze_trending_reason(self, repo_full_name: str) -> Dict:
        """分析某仓库为何热门（基于 GitHub API：近期提交、README、topics 等）。"""
        if not self.github:
            return {"error": "GITHUB_TOKEN is required"}
        try:
            repo = self.github.get_repo(repo_full_name)
            commits = list(repo.get_commits()[:10])
            recent_activity = len(commits)
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode("utf-8", errors="replace")[:500]
            except Exception:
                readme_content = "N/A"
            topics = repo.get_topics()
            return {
                "recent_commits": recent_activity,
                "readme_preview": readme_content,
                "topics": topics,
                "stars_today": repo.stargazers_count,
                "forks": repo.forks_count,
            }
        except Exception as e:
            return {"error": str(e)}
