"""
HubMind Main Agent - LangChain Integration
"""
from typing import List, Dict, Optional, Any
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.utils.llm_factory import LLMFactory
from config import Config


class HubMindAgent:
    """Main HubMind Agent powered by LangChain"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Initialize HubMind Agent

        Args:
            provider: LLM provider (openai, anthropic, google, azure, ollama, groq)
            model_name: Model name (optional, uses provider default if not provided)
            temperature: Model temperature
        """
        Config.validate()

        # Use config provider if not specified
        provider = provider or Config.LLM_PROVIDER
        model_name = model_name or Config.LLM_MODEL or None

        self.llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )

        # Initialize tools
        self.trending_tool = GitHubTrendingTool()
        self.pr_tool = GitHubPRTool()
        self.issue_tool = GitHubIssueTool()

        # Create LangChain tools
        self.tools = self._create_tools()

        # Create agent using LangChain 1.2+ API
        self.agent = self._create_agent()

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from GitHub tools"""
        return [
            Tool(
                name="get_trending_repos",
                func=self._get_trending_repos_wrapper,
                description=(
                    "Get trending GitHub repositories. "
                    "Input should be a JSON string with 'language' (optional), 'since' (daily/weekly/monthly), and 'limit' (default 10). "
                    "Example: '{\"language\": \"python\", \"since\": \"daily\", \"limit\": 10}'"
                )
            ),
            Tool(
                name="get_valuable_prs",
                func=self._get_valuable_prs_wrapper,
                description=(
                    "Get most valuable pull requests for a repository today. "
                    "Input should be the repository full name (owner/repo). "
                    "Example: 'microsoft/vscode'"
                )
            ),
            Tool(
                name="get_today_prs",
                func=self._get_today_prs_wrapper,
                description=(
                    "Get all pull requests updated today for a repository. "
                    "Input should be the repository full name (owner/repo). "
                    "Example: 'facebook/react'"
                )
            ),
            Tool(
                name="analyze_pr",
                func=self._analyze_pr_wrapper,
                description=(
                    "Get detailed analysis of a specific pull request. "
                    "Input should be a JSON string with 'repo' and 'pr_number'. "
                    "Example: '{\"repo\": \"microsoft/vscode\", \"pr_number\": 12345}'"
                )
            ),
            Tool(
                name="create_issue",
                func=self._create_issue_wrapper,
                description=(
                    "Create a new GitHub issue from natural language text. "
                    "Input should be a JSON string with 'repo' and 'text'. "
                    "Optional: 'assignees' (list) and 'labels' (list). "
                    "Example: '{\"repo\": \"microsoft/vscode\", \"text\": \"Add dark mode support\"}'"
                )
            ),
            Tool(
                name="get_issues",
                func=self._get_issues_wrapper,
                description=(
                    "Get issues for a repository. "
                    "Input should be a JSON string with 'repo', 'state' (open/closed/all), and optional 'limit'. "
                    "Example: '{\"repo\": \"microsoft/vscode\", \"state\": \"open\", \"limit\": 20}'"
                )
            ),
            Tool(
                name="analyze_trending_reason",
                func=self._analyze_trending_reason_wrapper,
                description=(
                    "Analyze why a repository is trending. "
                    "Input should be the repository full name (owner/repo). "
                    "Example: 'openai/gpt-4'"
                )
            ),
        ]

    def _create_agent(self):
        """
        Create the LangChain agent using Model I/O unified interface (LangChain 1.2+)
        """
        system_prompt = """You are HubMind, an intelligent GitHub assistant.
You help users discover trending repositories, analyze pull requests, and manage issues.

Your capabilities:
1. Find trending GitHub repositories (by language, time range)
2. Analyze pull requests and identify valuable ones
3. Create issues from natural language descriptions
4. Answer questions about repositories and code

Always be helpful, concise, and provide actionable insights. When showing results, format them nicely with clear sections."""

        # Use LangChain 1.2+ create_agent API (unified for all LLMs)
        return create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            debug=True
        )

    def _supports_tool_calling(self) -> bool:
        """Check if the LLM supports tool calling"""
        # Most modern LLMs support tool calling
        # OpenAI, Anthropic, Google Gemini, DeepSeek, etc. all support it
        provider = Config.LLM_PROVIDER.lower()
        tool_calling_providers = ["deepseek", "openai", "anthropic", "google", "azure", "groq"]
        return provider in tool_calling_providers

    # Tool wrapper methods
    def _get_trending_repos_wrapper(self, input_str: str) -> str:
        """Wrapper for get_trending_repos tool"""
        import json
        try:
            params = json.loads(input_str)
            repos = self.trending_tool.get_trending_repos(
                language=params.get("language"),
                since=params.get("since", "daily"),
                limit=params.get("limit", 10)
            )
            return self.trending_tool.get_trending_summary(repos)
        except json.JSONDecodeError:
            # If not JSON, try as simple string
            repos = self.trending_tool.get_trending_repos(limit=10)
            return self.trending_tool.get_trending_summary(repos)
        except Exception as e:
            return f"Error: {str(e)}"

    def _get_valuable_prs_wrapper(self, repo: str) -> str:
        """Wrapper for get_valuable_prs tool"""
        try:
            prs = self.pr_tool.get_valuable_prs(repo)
            if not prs or "error" in prs[0]:
                return f"No valuable PRs found for {repo} today."

            result = f"Most valuable PRs for {repo} today:\n\n"
            for i, pr in enumerate(prs, 1):
                result += f"{i}. **#{pr['number']}** {pr['title']} (Score: {pr['value_score']})\n"
                result += f"   Author: {pr['author']} | Comments: {pr['comments']} | State: {pr['state']}\n"
                result += f"   URL: {pr['url']}\n\n"

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def _get_today_prs_wrapper(self, repo: str) -> str:
        """Wrapper for get_today_prs tool"""
        try:
            prs = self.pr_tool.get_today_prs(repo)
            if not prs or "error" in prs[0]:
                return f"No PRs found for {repo} today."

            result = f"Today's PRs for {repo}:\n\n"
            for pr in prs:
                result += f"**#{pr['number']}** {pr['title']}\n"
                result += f"Author: {pr['author']} | State: {pr['state']} | Comments: {pr['comments']}\n"
                result += f"URL: {pr['url']}\n\n"

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def _analyze_pr_wrapper(self, input_str: str) -> str:
        """Wrapper for analyze_pr tool"""
        import json
        try:
            params = json.loads(input_str)
            analysis = self.pr_tool.analyze_pr(
                params["repo"],
                params["pr_number"]
            )

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
            return f"Error: {str(e)}"

    def _create_issue_wrapper(self, input_str: str) -> str:
        """Wrapper for create_issue tool"""
        import json
        try:
            params = json.loads(input_str)
            result = self.issue_tool.create_issue_from_text(
                params["repo"],
                params["text"],
                assignees=params.get("assignees"),
                labels=params.get("labels")
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
            return f"Error: {str(e)}"

    def _get_issues_wrapper(self, input_str: str) -> str:
        """Wrapper for get_issues tool"""
        import json
        try:
            params = json.loads(input_str)
            issues = self.issue_tool.get_issues(
                params["repo"],
                state=params.get("state", "open"),
                limit=params.get("limit", 20)
            )

            if not issues or "error" in issues[0]:
                return f"No issues found for {params['repo']}."

            result = f"Issues for {params['repo']} ({params.get('state', 'open')}):\n\n"
            for issue in issues:
                result += f"**#{issue['number']}** {issue['title']}\n"
                result += f"Author: {issue['author']} | Labels: {', '.join(issue['labels'])}\n"
                result += f"URL: {issue['url']}\n\n"

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def _analyze_trending_reason_wrapper(self, repo: str) -> str:
        """Wrapper for analyze_trending_reason tool"""
        try:
            analysis = self.trending_tool.analyze_trending_reason(repo)

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
            return f"Error: {str(e)}"

    def chat(self, message: str, chat_history: Optional[List] = None) -> str:
        """
        Chat with the agent

        Args:
            message: User message
            chat_history: Previous conversation history

        Returns:
            Agent response
        """
        try:
            # LangChain 1.2+ agent invocation
            config = {"configurable": {"thread_id": "1"}}
            result = self.agent.invoke({"messages": [HumanMessage(content=message)]}, config)

            # Extract response from agent output
            if isinstance(result, dict):
                if "messages" in result:
                    last_message = result["messages"][-1]
                    return last_message.content if hasattr(last_message, "content") else str(last_message)
                elif "output" in result:
                    return result["output"]
                else:
                    return str(result)
            else:
                return str(result)
        except Exception as e:
            return f"Error processing request: {str(e)}"
