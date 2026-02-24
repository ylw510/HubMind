"""
Automation and Workflow Utilities
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class AutomationWorkflow:
    """Automation workflows for GitHub operations"""

    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN)

    def batch_label_issues(
        self,
        repo_full_name: str,
        label: str,
        issue_numbers: List[int]
    ) -> Dict:
        """
        Add a label to multiple issues

        Args:
            repo_full_name: Repository full name (owner/repo)
            label: Label name to add
            issue_numbers: List of issue numbers

        Returns:
            Operation result
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            results = {
                "success": [],
                "failed": []
            }

            for issue_num in issue_numbers:
                try:
                    issue = repo.get_issue(issue_num)
                    issue.add_to_labels(label)
                    results["success"].append(issue_num)
                except Exception as e:
                    results["failed"].append({
                        "issue": issue_num,
                        "error": str(e)
                    })

            return results
        except Exception as e:
            return {"error": str(e)}

    def close_stale_issues(
        self,
        repo_full_name: str,
        days_inactive: int = 90,
        label: Optional[str] = None
    ) -> Dict:
        """
        Close stale issues that haven't been updated

        Args:
            repo_full_name: Repository full name (owner/repo)
            days_inactive: Days of inactivity to consider stale
            label: Optional label to filter by

        Returns:
            Operation result
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            cutoff_date = datetime.now() - timedelta(days=days_inactive)

            closed_issues = []
            skipped_issues = []

            issues = repo.get_issues(state="open", sort="updated", direction="asc")

            for issue in issues:
                # Skip if has label filter and doesn't match
                if label:
                    issue_labels = [l.name for l in issue.labels]
                    if label not in issue_labels:
                        continue

                # Check if stale
                if issue.updated_at < cutoff_date:
                    try:
                        issue.edit(state="closed")
                        closed_issues.append({
                            "number": issue.number,
                            "title": issue.title,
                            "last_updated": issue.updated_at.isoformat()
                        })
                    except Exception as e:
                        skipped_issues.append({
                            "number": issue.number,
                            "error": str(e)
                        })

            return {
                "closed": len(closed_issues),
                "skipped": len(skipped_issues),
                "closed_issues": closed_issues,
                "skipped_issues": skipped_issues
            }
        except Exception as e:
            return {"error": str(e)}

    def invite_contributor(
        self,
        repo_full_name: str,
        username: str,
        permission: str = "push"
    ) -> Dict:
        """
        Invite a user as a collaborator

        Args:
            repo_full_name: Repository full name (owner/repo)
            username: GitHub username
            permission: Permission level (pull, push, admin)

        Returns:
            Invitation result
        """
        try:
            repo = self.github.get_repo(repo_full_name)

            # Check if user is already a collaborator
            try:
                collab = repo.get_collaborator(username)
                return {
                    "status": "already_collaborator",
                    "username": username,
                    "permission": collab.permissions
                }
            except:
                pass

            # Add collaborator
            repo.add_to_collaborators(username, permission)

            return {
                "status": "invited",
                "username": username,
                "permission": permission
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_weekly_report(
        self,
        repo_full_name: str
    ) -> Dict:
        """
        Generate a weekly activity report

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            Weekly report dictionary
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            week_ago = datetime.now() - timedelta(days=7)

            # Get PRs
            prs = [pr for pr in repo.get_pulls(state="all")
                  if pr.created_at >= week_ago]

            # Get issues
            issues = [issue for issue in repo.get_issues(state="all")
                     if issue.created_at >= week_ago]

            # Get commits
            commits = list(repo.get_commits(since=week_ago))

            # Get contributors
            contributors = {}
            for commit in commits:
                author = commit.author
                if author:
                    contributors[author.login] = contributors.get(author.login, 0) + 1

            return {
                "repo": repo_full_name,
                "period": "7 days",
                "new_prs": len([pr for pr in prs if pr.state == "open"]),
                "merged_prs": len([pr for pr in prs if pr.state == "merged"]),
                "closed_prs": len([pr for pr in prs if pr.state == "closed"]),
                "new_issues": len([issue for issue in issues if issue.state == "open"]),
                "closed_issues": len([issue for issue in issues if issue.state == "closed"]),
                "commits": len(commits),
                "contributors": len(contributors),
                "top_contributors": sorted(
                    contributors.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            }
        except Exception as e:
            return {"error": str(e)}
