"""
HubMind Usage Examples
This file demonstrates how to use HubMind programmatically
"""
from src.agents.hubmind_agent import HubMindAgent
from src.agents.qa_agent import HubMindQAAgent
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.utils.dashboard import DeveloperDashboard
from src.utils.automation import AutomationWorkflow


def example_trending():
    """Example: Get trending repositories"""
    print("=" * 50)
    print("Example 1: Get Trending Repositories")
    print("=" * 50)

    tool = GitHubTrendingTool()
    repos = tool.get_trending_repos(language="python", since="daily", limit=5)

    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['name']} - {repo['stars']} ⭐")
        print(f"   {repo['description']}")
        print()


def example_pr_analysis():
    """Example: Analyze valuable PRs"""
    print("=" * 50)
    print("Example 2: Analyze Valuable PRs")
    print("=" * 50)

    tool = GitHubPRTool()
    prs = tool.get_valuable_prs("microsoft/vscode", limit=5)

    for pr in prs:
        print(f"PR #{pr['number']}: {pr['title']}")
        print(f"  Score: {pr['value_score']} | Comments: {pr['comments']}")
        print(f"  URL: {pr['url']}")
        print()


def example_create_issue():
    """Example: Create issue from natural language"""
    print("=" * 50)
    print("Example 3: Create Issue (commented out - requires repo access)")
    print("=" * 50)

    # Uncomment and provide a valid repo you have access to
    # tool = GitHubIssueTool()
    # result = tool.create_issue_from_text(
    #     "your-username/your-repo",
    #     "Add support for Python 3.12"
    # )
    # print(f"Issue created: {result['url']}")

    print("(This example is commented out to avoid creating real issues)")
    print("Uncomment the code and provide a valid repository to test.")


def example_qa():
    """Example: Ask questions about a repository"""
    print("=" * 50)
    print("Example 4: Ask Questions About Repository")
    print("=" * 50)

    qa_agent = HubMindQAAgent()
    result = qa_agent.answer_repo_question(
        "microsoft/vscode",
        "What programming language is this project written in?"
    )

    print(f"Question: {result['question']}")
    print(f"Answer: {result['answer']}")
    print()


def example_health_dashboard():
    """Example: Get repository health metrics"""
    print("=" * 50)
    print("Example 5: Repository Health Dashboard")
    print("=" * 50)

    dashboard = DeveloperDashboard()
    health = dashboard.get_repo_health("microsoft/vscode", days=30)

    if "error" not in health:
        print(f"Repository: {health['repo']}")
        print(f"PR Merge Rate: {health['pr_merge_rate']}%")
        print(f"Active Contributors: {health['active_contributors']}")
        print(f"Commits per Day: {health['commits_per_day']}")
        print(f"Top Contributors: {', '.join(health['contributor_list'][:5])}")
    else:
        print(f"Error: {health['error']}")
    print()


def example_chat_agent():
    """Example: Chat with HubMind agent"""
    print("=" * 50)
    print("Example 6: Chat with HubMind Agent")
    print("=" * 50)

    agent = HubMindAgent()

    questions = [
        "What are the top 3 trending Python projects today?",
        "Show me valuable PRs in microsoft/vscode",
    ]

    for question in questions:
        print(f"\nQ: {question}")
        response = agent.chat(question)
        print(f"A: {response[:200]}...")  # Truncate for display
        print()


def example_automation():
    """Example: Automation workflows"""
    print("=" * 50)
    print("Example 7: Automation Workflows")
    print("=" * 50)

    automation = AutomationWorkflow()

    # Generate weekly report
    report = automation.generate_weekly_report("microsoft/vscode")

    if "error" not in report:
        print(f"Weekly Report for {report['repo']}:")
        print(f"  New PRs: {report['new_prs']}")
        print(f"  Merged PRs: {report['merged_prs']}")
        print(f"  New Issues: {report['new_issues']}")
        print(f"  Commits: {report['commits']}")
        print(f"  Contributors: {report['contributors']}")
    else:
        print(f"Error: {report['error']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("HubMind Examples")
    print("=" * 50 + "\n")

    try:
        example_trending()
        example_pr_analysis()
        example_create_issue()
        example_qa()
        example_health_dashboard()
        example_chat_agent()
        example_automation()

        print("\n" + "=" * 50)
        print("All examples completed!")
        print("=" * 50)
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure you have:")
        print("1. Set GITHUB_TOKEN in .env file")
        print("2. Set OPENAI_API_KEY in .env file")
        print("3. Installed all dependencies: pip install -r requirements.txt")
