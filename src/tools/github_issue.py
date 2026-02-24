"""
GitHub Issue Management Tools
"""
from typing import List, Dict, Optional
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config


class GitHubIssueTool:
    """Tool for managing GitHub Issues"""

    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN)

    def create_issue_from_text(
        self,
        repo_full_name: str,
        text: str,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict:
        """
        Create an issue from natural language text

        Args:
            repo_full_name: Repository full name (owner/repo)
            text: Natural language description of the issue
            assignees: List of usernames to assign
            labels: List of labels to add

        Returns:
            Created issue information
        """
        try:
            repo = self.github.get_repo(repo_full_name)

            # Parse text to extract title and body
            parsed = self._parse_issue_text(text)

            # Check for similar issues
            similar_issues = self._find_similar_issues(repo, parsed["title"])

            # Create issue
            issue = repo.create_issue(
                title=parsed["title"],
                body=parsed["body"],
                assignees=assignees or [],
                labels=labels or parsed.get("suggested_labels", [])
            )

            return {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url,
                "similar_issues": similar_issues,
                "labels": [label.name for label in issue.labels],
            }
        except Exception as e:
            return {"error": str(e)}

    def get_issues(
        self,
        repo_full_name: str,
        state: str = "open",
        limit: int = 20
    ) -> List[Dict]:
        """
        Get issues for a repository

        Args:
            repo_full_name: Repository full name (owner/repo)
            state: Issue state ('open', 'closed', 'all')
            limit: Maximum number of issues to return

        Returns:
            List of issue information
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            issues = []

            for issue in repo.get_issues(state=state, sort="updated", direction="desc"):
                issues.append(self._issue_to_dict(issue))
                if len(issues) >= limit:
                    break

            return issues
        except Exception as e:
            return [{"error": str(e)}]

    def classify_issue(self, text: str) -> Dict:
        """
        Classify issue type (bug/feature/docs/question)

        Args:
            text: Issue description text

        Returns:
            Classification result
        """
        text_lower = text.lower()

        # Simple keyword-based classification
        issue_type = "question"
        priority = "medium"

        bug_keywords = ["bug", "error", "crash", "broken", "fail", "issue", "problem"]
        feature_keywords = ["feature", "add", "implement", "new", "enhancement", "improve"]
        doc_keywords = ["doc", "documentation", "readme", "guide", "tutorial"]
        urgent_keywords = ["urgent", "critical", "blocking", "broken", "crash"]

        if any(keyword in text_lower for keyword in bug_keywords):
            issue_type = "bug"
        elif any(keyword in text_lower for keyword in feature_keywords):
            issue_type = "feature"
        elif any(keyword in text_lower for keyword in doc_keywords):
            issue_type = "documentation"

        if any(keyword in text_lower for keyword in urgent_keywords):
            priority = "high"

        return {
            "type": issue_type,
            "priority": priority,
            "suggested_labels": [issue_type, priority]
        }

    def _parse_issue_text(self, text: str) -> Dict:
        """
        Parse natural language text into issue title and body

        Args:
            text: Natural language description

        Returns:
            Parsed issue data
        """
        # Simple parsing - can be enhanced with NLP
        lines = text.strip().split('\n')
        title = lines[0] if lines else text[:100]

        # If title is too long, truncate it
        if len(title) > 100:
            title = title[:97] + "..."

        body = '\n'.join(lines[1:]) if len(lines) > 1 else text

        # Classify issue
        classification = self.classify_issue(text)

        # Add classification to body
        if body:
            body = f"**Type:** {classification['type']}\n**Priority:** {classification['priority']}\n\n{body}"
        else:
            body = f"**Type:** {classification['type']}\n**Priority:** {classification['priority']}"

        return {
            "title": title,
            "body": body,
            "suggested_labels": classification["suggested_labels"]
        }

    def _find_similar_issues(
        self,
        repo,
        title: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar issues to avoid duplicates

        Args:
            repo: GitHub repository object
            title: Issue title to search for
            limit: Maximum number of similar issues to return

        Returns:
            List of similar issues
        """
        try:
            # Search for issues with similar keywords
            keywords = title.lower().split()[:3]  # Use first 3 words
            query = " ".join(keywords)

            similar = []
            for issue in repo.get_issues(state="open", sort="updated", direction="desc"):
                if any(keyword in issue.title.lower() for keyword in keywords):
                    similar.append({
                        "number": issue.number,
                        "title": issue.title,
                        "url": issue.html_url,
                    })
                    if len(similar) >= limit:
                        break

            return similar
        except:
            return []

    def _issue_to_dict(self, issue) -> Dict:
        """Convert issue object to dictionary"""
        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "author": issue.user.login,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "comments": issue.comments,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "url": issue.html_url,
        }
