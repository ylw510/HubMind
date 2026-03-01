"""
LangChain Tools Module - 使用 LangChain 的现代工具 API 重构工具调用
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, StructuredTool
from langchain_core.tools.base import BaseTool

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== Pydantic Models for Tool Inputs ==========

class GetTrendingReposInput(BaseModel):
    """Input for get_trending_repos tool"""
    language: Optional[str] = Field(None, description="Programming language filter (e.g., 'python', 'javascript')")
    since: str = Field("daily", description="Time range: 'daily', 'weekly', or 'monthly'")
    limit: int = Field(10, description="Maximum number of repositories to return")


class GetValuablePRsInput(BaseModel):
    """Input for get_valuable_prs tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")


class GetTodayPRsInput(BaseModel):
    """Input for get_today_prs tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")


class AnalyzePRInput(BaseModel):
    """Input for analyze_pr tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")
    pr_number: int = Field(..., description="Pull request number")


class CreateIssueInput(BaseModel):
    """Input for create_issue tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")
    text: str = Field(..., description="Natural language description of the issue")
    assignees: Optional[List[str]] = Field(None, description="List of usernames to assign")
    labels: Optional[List[str]] = Field(None, description="List of labels to add")


class GetIssuesInput(BaseModel):
    """Input for get_issues tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")
    state: str = Field("open", description="Issue state: 'open', 'closed', or 'all'")
    limit: int = Field(20, description="Maximum number of issues to return")


class AnalyzeTrendingReasonInput(BaseModel):
    """Input for analyze_trending_reason tool"""
    repo: str = Field(..., description="Repository full name (owner/repo)")


# ========== Tool Factory Functions ==========

def create_github_tools(
    trending_tool: GitHubTrendingTool,
    pr_tool: GitHubPRTool,
    issue_tool: GitHubIssueTool
) -> List[BaseTool]:
    """
    Create LangChain tools from GitHub tools using modern @tool decorator

    Args:
        trending_tool: GitHubTrendingTool instance
        pr_tool: GitHubPRTool instance
        issue_tool: GitHubIssueTool instance

    Returns:
        List of LangChain tools
    """

    # Tool 1: Get Trending Repositories
    @tool(args_schema=GetTrendingReposInput)
    def get_trending_repos(
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10
    ) -> str:
        """
        Get trending GitHub repositories with AI-powered summary.

        Args:
            language: Optional programming language filter (e.g., 'python', 'javascript')
            since: Time range - 'daily', 'weekly', or 'monthly' (default: 'daily')
            limit: Maximum number of repositories to return (default: 10)

        Returns:
            Formatted summary of trending repositories
        """
        try:
            repos = trending_tool.get_trending_repos(
                language=language,
                since=since,
                limit=limit
            )
            return trending_tool.get_trending_summary(
                repos, language=language, since=since, use_llm=True
            )
        except Exception as e:
            logger.error(f"Error in get_trending_repos: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 2: Get Valuable PRs
    @tool(args_schema=GetValuablePRsInput)
    def get_valuable_prs(repo: str) -> str:
        """
        Get the most valuable pull requests for a repository today.
        Valuable PRs are determined by engagement (comments, reviews) and code changes.

        Args:
            repo: Repository full name in format 'owner/repo' (e.g., 'microsoft/vscode')

        Returns:
            Formatted list of valuable PRs with scores
        """
        try:
            prs = pr_tool.get_valuable_prs(repo)
            if not prs or "error" in prs[0]:
                return f"No valuable PRs found for {repo} today."

            result = f"Most valuable PRs for {repo} today:\n\n"
            for i, pr in enumerate(prs, 1):
                result += f"{i}. **#{pr['number']}** {pr['title']} (Score: {pr['value_score']})\n"
                result += f"   Author: {pr['author']} | Comments: {pr['comments']} | State: {pr['state']}\n"
                result += f"   URL: {pr['url']}\n\n"

            return result
        except Exception as e:
            logger.error(f"Error in get_valuable_prs: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 3: Get Today's PRs
    @tool(args_schema=GetTodayPRsInput)
    def get_today_prs(repo: str) -> str:
        """
        Get all pull requests updated today for a repository.

        Args:
            repo: Repository full name in format 'owner/repo' (e.g., 'facebook/react')

        Returns:
            Formatted list of today's PRs
        """
        try:
            prs = pr_tool.get_today_prs(repo)
            if not prs or "error" in prs[0]:
                return f"No PRs found for {repo} today."

            result = f"Today's PRs for {repo}:\n\n"
            for pr in prs:
                result += f"**#{pr['number']}** {pr['title']}\n"
                result += f"Author: {pr['author']} | State: {pr['state']} | Comments: {pr['comments']}\n"
                result += f"URL: {pr['url']}\n\n"

            return result
        except Exception as e:
            logger.error(f"Error in get_today_prs: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 4: Analyze PR
    @tool(args_schema=AnalyzePRInput)
    def analyze_pr(repo: str, pr_number: int) -> str:
        """
        Get detailed analysis of a specific pull request including value score,
        code changes, engagement metrics, and maintainer participation.

        Args:
            repo: Repository full name in format 'owner/repo'
            pr_number: Pull request number

        Returns:
            Detailed PR analysis report
        """
        try:
            analysis = pr_tool.analyze_pr(repo, pr_number)

            if "error" in analysis:
                return f"Error: {analysis['error']}"

            result = f"PR Analysis for #{analysis['number']}: {analysis['title']}\n\n"
            result += f"State: {analysis['state']} | Author: {analysis['author']}\n"
            result += f"Value Score: {analysis['value_score']}\n"
            result += f"Files Changed: {analysis['files_changed']}\n"
            result += f"Additions: +{analysis['additions']} | Deletions: -{analysis['deletions']}\n"
            result += f"Comments: {analysis['comments']} | Review Comments: {analysis['review_comments']}\n"
            result += f"Maintainer Participated: {analysis['maintainer_participated']}\n"
            result += f"URL: {analysis['url']}\n"

            return result
        except Exception as e:
            logger.error(f"Error in analyze_pr: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 5: Create Issue
    @tool(args_schema=CreateIssueInput)
    def create_issue(
        repo: str,
        text: str,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> str:
        """
        Create a new GitHub issue from natural language text.
        The tool will automatically parse the text to extract title and description,
        classify the issue type, and suggest appropriate labels.

        Args:
            repo: Repository full name in format 'owner/repo'
            text: Natural language description of the issue
            assignees: Optional list of usernames to assign to the issue
            labels: Optional list of labels to add to the issue

        Returns:
            Created issue information with URL and similar issues warning
        """
        try:
            result = issue_tool.create_issue_from_text(
                repo,
                text,
                assignees=assignees,
                labels=labels
            )

            if "error" in result:
                return f"Error: {result['error']}"

            response = f"Issue created successfully!\n\n"
            response += f"**#{result['number']}** {result['title']}\n"
            response += f"URL: {result['url']}\n"
            response += f"Labels: {', '.join(result['labels'])}\n"

            if result.get("similar_issues"):
                response += f"\n⚠️ Similar issues found: {len(result['similar_issues'])}\n"
                for similar in result['similar_issues'][:3]:
                    response += f"- #{similar['number']}: {similar['title']}\n"

            return response
        except Exception as e:
            logger.error(f"Error in create_issue: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 6: Get Issues
    @tool(args_schema=GetIssuesInput)
    def get_issues(
        repo: str,
        state: str = "open",
        limit: int = 20
    ) -> str:
        """
        Get issues for a repository, filtered by state.

        Args:
            repo: Repository full name in format 'owner/repo'
            state: Issue state - 'open', 'closed', or 'all' (default: 'open')
            limit: Maximum number of issues to return (default: 20)

        Returns:
            Formatted list of issues
        """
        try:
            issues = issue_tool.get_issues(repo, state=state, limit=limit)

            if not issues or "error" in issues[0]:
                return f"No issues found for {repo}."

            result = f"Issues for {repo} ({state}):\n\n"
            for issue in issues:
                result += f"**#{issue['number']}** {issue['title']}\n"
                result += f"Author: {issue['author']} | Labels: {', '.join(issue['labels'])}\n"
                result += f"URL: {issue['url']}\n\n"

            return result
        except Exception as e:
            logger.error(f"Error in get_issues: {str(e)}")
            return f"Error: {str(e)}"

    # Tool 7: Analyze Trending Reason
    @tool(args_schema=AnalyzeTrendingReasonInput)
    def analyze_trending_reason(repo: str) -> str:
        """
        Analyze why a repository is trending by examining recent commits,
        stars, forks, topics, and README content.

        Args:
            repo: Repository full name in format 'owner/repo' (e.g., 'openai/gpt-4')

        Returns:
            Analysis report explaining why the repository is trending
        """
        try:
            analysis = trending_tool.analyze_trending_reason(repo)

            if "error" in analysis:
                return f"Error: {analysis['error']}"

            result = f"Trending Analysis for {repo}:\n\n"
            result += f"Recent Commits: {analysis['recent_commits']}\n"
            result += f"Stars: {analysis['stars_today']} | Forks: {analysis['forks']}\n"
            result += f"Topics: {', '.join(analysis['topics'])}\n"
            if analysis.get('readme_preview'):
                result += f"\nREADME Preview:\n{analysis['readme_preview'][:200]}...\n"

            return result
        except Exception as e:
            logger.error(f"Error in analyze_trending_reason: {str(e)}")
            return f"Error: {str(e)}"

    # Return all tools
    return [
        get_trending_repos,
        get_valuable_prs,
        get_today_prs,
        analyze_pr,
        create_issue,
        get_issues,
        analyze_trending_reason,
    ]
