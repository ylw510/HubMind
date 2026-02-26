"""
Developer Dashboard Utilities
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class DeveloperDashboard:
    """Developer dashboard for monitoring repositories"""

    def __init__(self, github_token: Optional[str] = None):
        token = github_token or Config.GITHUB_TOKEN
        self.github = Github(token)

    def get_repo_health(
        self,
        repo_full_name: str,
        days: int = 30
    ) -> Dict:
        """
        Get repository health metrics

        Args:
            repo_full_name: Repository full name (owner/repo)
            days: Number of days to analyze

        Returns:
            Health metrics dictionary
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            since_date = datetime.now() - timedelta(days=days)

            # Issue response time
            open_issues = list(repo.get_issues(state="open", sort="updated"))
            avg_response_time = self._calculate_avg_response_time(open_issues, since_date)

            # PR merge rate
            prs = list(repo.get_pulls(state="all"))
            merge_rate = self._calculate_merge_rate(prs, since_date)

            # Active contributors
            contributors = self._get_active_contributors(repo, since_date)

            # Commit frequency
            commits = list(repo.get_commits(since=since_date))
            commit_frequency = len(commits) / days if days > 0 else 0

            return {
                "repo": repo_full_name,
                "period_days": days,
                "avg_issue_response_hours": avg_response_time,
                "pr_merge_rate": merge_rate,
                "active_contributors": len(contributors),
                "contributor_list": contributors[:10],
                "commits_per_day": round(commit_frequency, 2),
                "total_commits": len(commits),
                "open_issues": repo.open_issues_count,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_watched_repos_activity(
        self,
        repo_list: List[str],
        hours: int = 24
    ) -> List[Dict]:
        """
        Get activity for watched repositories

        Args:
            repo_list: List of repository full names
            hours: Hours to look back

        Returns:
            List of activity summaries
        """
        activities = []
        since = datetime.now() - timedelta(hours=hours)

        for repo_name in repo_list:
            try:
                repo = self.github.get_repo(repo_name)

                # Recent PRs
                recent_prs = [pr for pr in repo.get_pulls(state="all")
                             if pr.updated_at >= since]

                # Recent issues
                recent_issues = [issue for issue in repo.get_issues(state="all")
                               if issue.updated_at >= since]

                # Recent commits
                recent_commits = [c for c in repo.get_commits(since=since)]

                activities.append({
                    "repo": repo_name,
                    "new_prs": len([pr for pr in recent_prs if pr.created_at >= since]),
                    "updated_prs": len(recent_prs),
                    "new_issues": len([issue for issue in recent_issues if issue.created_at >= since]),
                    "updated_issues": len(recent_issues),
                    "commits": len(recent_commits),
                })
            except Exception as e:
                activities.append({
                    "repo": repo_name,
                    "error": str(e)
                })

        return activities

    def _calculate_avg_response_time(
        self,
        issues: List,
        since_date: datetime
    ) -> float:
        """Calculate average issue response time in hours"""
        response_times = []

        for issue in issues:
            if issue.comments > 0:
                comments = list(issue.get_comments())
                if comments:
                    first_response = comments[0].created_at
                    response_time = (first_response - issue.created_at).total_seconds() / 3600
                    if response_time > 0:
                        response_times.append(response_time)

        if response_times:
            return round(sum(response_times) / len(response_times), 2)
        return 0.0

    def _calculate_merge_rate(
        self,
        prs: List,
        since_date: datetime
    ) -> float:
        """Calculate PR merge rate percentage"""
        recent_prs = [pr for pr in prs if pr.created_at >= since_date]
        if not recent_prs:
            return 0.0

        merged = sum(1 for pr in recent_prs if pr.state == "merged")
        return round((merged / len(recent_prs)) * 100, 2)

    def _get_active_contributors(
        self,
        repo,
        since_date: datetime
    ) -> List[str]:
        """Get list of active contributors"""
        contributors = {}

        try:
            commits = list(repo.get_commits(since=since_date))
            for commit in commits:
                author = commit.author
                if author:
                    contributors[author.login] = contributors.get(author.login, 0) + 1
        except:
            pass

        # Sort by commit count
        sorted_contributors = sorted(
            contributors.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [name for name, _ in sorted_contributors]
