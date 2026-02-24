"""
GitHub PR Analysis Tools
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class GitHubPRTool:
    """Tool for analyzing GitHub Pull Requests"""

    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN)

    def get_today_prs(
        self,
        repo_full_name: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get today's pull requests for a repository

        Args:
            repo_full_name: Repository full name (owner/repo)
            limit: Maximum number of PRs to return

        Returns:
            List of PR information
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            today = datetime.now().date()

            prs = []
            for pr in repo.get_pulls(state="all", sort="updated", direction="desc"):
                if pr.updated_at.date() == today:
                    prs.append(self._pr_to_dict(pr))
                    if len(prs) >= limit:
                        break

            return prs
        except Exception as e:
            return [{"error": str(e)}]

    def get_valuable_prs(
        self,
        repo_full_name: str,
        limit: int = 10,
        min_comments: int = 3
    ) -> List[Dict]:
        """
        Get most valuable PRs based on engagement and code changes

        Args:
            repo_full_name: Repository full name (owner/repo)
            limit: Maximum number of PRs to return
            min_comments: Minimum comments to consider valuable

        Returns:
            List of valuable PRs sorted by value score
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            today = datetime.now().date()

            prs = []
            for pr in repo.get_pulls(state="all", sort="updated", direction="desc"):
                if pr.updated_at.date() == today:
                    pr_dict = self._pr_to_dict(pr)
                    pr_dict["value_score"] = self._calculate_value_score(pr)
                    if pr_dict["comments"] >= min_comments:
                        prs.append(pr_dict)

            # Sort by value score
            prs.sort(key=lambda x: x["value_score"], reverse=True)
            return prs[:limit]
        except Exception as e:
            return [{"error": str(e)}]

    def analyze_pr(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> Dict:
        """
        Detailed analysis of a specific PR

        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number

        Returns:
            Detailed PR analysis
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            # Get files changed
            files = pr.get_files()
            file_changes = []
            total_additions = 0
            total_deletions = 0

            for file in files:
                file_changes.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                })
                total_additions += file.additions
                total_deletions += file.deletions

            # Get reviews
            reviews = pr.get_reviews()
            review_summary = {
                "total": reviews.totalCount,
                "approved": sum(1 for r in reviews if r.state == "APPROVED"),
                "changes_requested": sum(1 for r in reviews if r.state == "CHANGES_REQUESTED"),
            }

            # Check for maintainer participation
            maintainers = [collab.login for collab in repo.get_collaborators()]
            maintainer_participated = any(
                comment.user.login in maintainers
                for comment in pr.get_issue_comments()
            )

            return {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "comments": pr.comments,
                "review_comments": pr.review_comments,
                "additions": total_additions,
                "deletions": total_deletions,
                "files_changed": len(file_changes),
                "file_details": file_changes,
                "review_summary": review_summary,
                "maintainer_participated": maintainer_participated,
                "value_score": self._calculate_value_score(pr),
                "url": pr.html_url,
            }
        except Exception as e:
            return {"error": str(e)}

    def detect_controversial_prs(
        self,
        repo_full_name: str,
        min_comments: int = 10
    ) -> List[Dict]:
        """
        Detect controversial PRs (high engagement with mixed opinions)

        Args:
            repo_full_name: Repository full name (owner/repo)
            min_comments: Minimum comments to consider

        Returns:
            List of controversial PRs
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            today = datetime.now().date()

            controversial = []
            for pr in repo.get_pulls(state="open", sort="comments", direction="desc"):
                if pr.updated_at.date() == today and pr.comments >= min_comments:
                    # Check for mixed review states
                    reviews = pr.get_reviews()
                    has_approved = any(r.state == "APPROVED" for r in reviews)
                    has_changes = any(r.state == "CHANGES_REQUESTED" for r in reviews)

                    if has_approved and has_changes:
                        pr_dict = self._pr_to_dict(pr)
                        pr_dict["controversy_score"] = pr.comments + pr.review_comments
                        controversial.append(pr_dict)

            return controversial
        except Exception as e:
            return [{"error": str(e)}]

    def _pr_to_dict(self, pr) -> Dict:
        """Convert PR object to dictionary"""
        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "comments": pr.comments,
            "review_comments": pr.review_comments,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "url": pr.html_url,
        }

    def _calculate_value_score(self, pr) -> float:
        """Calculate a value score for a PR"""
        score = 0.0

        # Comments and engagement
        score += pr.comments * 2
        score += pr.review_comments * 3

        # Code changes (balanced)
        if pr.additions > 0:
            score += min(pr.additions / 100, 10)  # Cap at 10 points
        if pr.deletions > 0:
            score += min(pr.deletions / 100, 5)  # Cap at 5 points

        # State bonus
        if pr.state == "merged":
            score += 20
        elif pr.state == "open":
            score += 5

        return round(score, 2)
