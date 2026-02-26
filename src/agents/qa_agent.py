"""
HubMind QA Agent - Repository and Code Question Answering
"""
from typing import Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from github import Github
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Config
from src.utils.llm_factory import LLMFactory
from typing import Optional


class HubMindQAAgent:
    """QA Agent for answering questions about repositories and code"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        github_token: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ):
        """
        Initialize QA Agent

        Args:
            provider: LLM provider (openai, anthropic, google, azure, ollama, groq, deepseek)
            model_name: Model name (optional, uses provider default if not provided)
            github_token: Optional override for GitHub token
            llm_api_key: Optional override for LLM API key
        """
        use_overrides = bool(github_token and llm_api_key)
        if not use_overrides:
            Config.validate()

        provider = provider or Config.LLM_PROVIDER
        model_name = model_name or Config.LLM_MODEL or None

        llm_kwargs = {}
        if llm_api_key:
            llm_kwargs["api_key"] = llm_api_key

        self.llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=0.2,
            **llm_kwargs
        )
        token = github_token or Config.GITHUB_TOKEN
        self.github = Github(token)

        self.qa_prompt_template = """You are a helpful GitHub repository assistant. Answer questions about repositories based on the provided context.

Context about the repository:
{context}

Question: {question}

Provide a clear, concise answer. If you don't have enough information, say so."""

    def answer_repo_question(
        self,
        repo_full_name: str,
        question: str
    ) -> Dict:
        """
        Answer a question about a repository

        Args:
            repo_full_name: Repository full name (owner/repo)
            question: Question to answer

        Returns:
            Answer dictionary
        """
        try:
            repo = self.github.get_repo(repo_full_name)

            # Gather context
            context = self._gather_repo_context(repo)

            # Generate answer using LLM directly
            prompt = self.qa_prompt_template.format(context=context, question=question)
            messages = [
                SystemMessage(content="You are a helpful GitHub repository assistant."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            answer = response.content if hasattr(response, "content") else str(response)

            return {
                "question": question,
                "answer": answer,
                "repo": repo_full_name,
                "sources": self._extract_sources(context)
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "repo": repo_full_name
            }

    def _gather_repo_context(self, repo) -> str:
        """Gather context about a repository"""
        context_parts = []

        # Basic info
        context_parts.append(f"Repository: {repo.full_name}")
        context_parts.append(f"Description: {repo.description or 'N/A'}")
        context_parts.append(f"Language: {repo.language or 'N/A'}")
        context_parts.append(f"Stars: {repo.stargazers_count}")
        context_parts.append(f"Forks: {repo.forks_count}")
        context_parts.append(f"Open Issues: {repo.open_issues_count}")

        # Topics
        topics = repo.get_topics()
        if topics:
            context_parts.append(f"Topics: {', '.join(topics)}")

        # README
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8')[:2000]
            context_parts.append(f"\nREADME (excerpt):\n{readme_content}")
        except:
            pass

        # Recent commits
        try:
            commits = list(repo.get_commits()[:5])
            context_parts.append("\nRecent commits:")
            for commit in commits:
                context_parts.append(f"- {commit.commit.message[:100]}")
        except:
            pass

        # Contributors
        try:
            contributors = list(repo.get_contributors()[:10])
            contributor_names = [c.login for c in contributors]
            context_parts.append(f"\nTop Contributors: {', '.join(contributor_names)}")
        except:
            pass

        # Files structure (top level)
        try:
            contents = repo.get_contents("")
            file_list = [item.name for item in contents if item.type == "file"][:20]
            context_parts.append(f"\nTop-level files: {', '.join(file_list)}")
        except:
            pass

        return "\n".join(context_parts)

    def _extract_sources(self, context: str) -> List[str]:
        """Extract source information from context"""
        sources = []
        lines = context.split('\n')
        for line in lines:
            if line.startswith("Repository:") or line.startswith("README") or line.startswith("Recent commits"):
                sources.append(line)
        return sources[:5]
