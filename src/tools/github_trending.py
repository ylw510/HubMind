"""
GitHub Trending Tools
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class GitHubTrendingTool:
    """Tool for fetching GitHub trending repositories"""

    def __init__(self, github_token: Optional[str] = None):
        token = github_token or Config.GITHUB_TOKEN
        self.github = Github(token)

    def get_trending_repos(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get trending repositories

        Args:
            language: Programming language filter (e.g., 'python', 'javascript')
            since: Time range ('daily', 'weekly', 'monthly')
            limit: Maximum number of repos to return

        Returns:
            List of trending repository information
        """
        # Note: GitHub API doesn't have a direct trending endpoint
        # We'll use search API with sort by stars and time filter
        since_date = self._get_since_date(since)
        query = f"created:>{since_date}"
        if language:
            query += f" language:{language}"

        repos = self.github.search_repositories(
            query=query,
            sort="stars",
            order="desc"
        )

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

    def get_trending_summary(self, repos: List[Dict]) -> str:
        """
        Generate a summary of trending repositories

        Args:
            repos: List of repository dictionaries

        Returns:
            Summary text
        """
        if not repos:
            return "No trending repositories found."

        summary = f"Found {len(repos)} trending repositories:\n\n"
        for i, repo in enumerate(repos, 1):
            summary += f"{i}. **{repo['name']}** ({repo['stars']} ⭐)\n"
            summary += f"   {repo['description']}\n"
            summary += f"   Language: {repo['language'] or 'N/A'}\n"
            summary += f"   URL: {repo['url']}\n\n"

        return summary

    def _get_since_date(self, since: str) -> str:
        """Convert since parameter to date string"""
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

    def analyze_trending_reason(self, repo_full_name: str) -> Dict:
        """
        Analyze why a repository is trending

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            Analysis dictionary
        """
        try:
            repo = self.github.get_repo(repo_full_name)

            # Get recent commits
            commits = list(repo.get_commits()[:10])
            recent_activity = len(commits)

            # Get README content
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode('utf-8')[:500]
            except:
                readme_content = "N/A"

            # Get topics
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
