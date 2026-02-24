"""
HubMind - GitHub Intelligent Agent
Main Entry Point
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional, List
import json

from src.agents.hubmind_agent import HubMindAgent
from src.agents.qa_agent import HubMindQAAgent
from src.utils.dashboard import DeveloperDashboard
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from config import Config

app = typer.Typer(help="HubMind - Your Intelligent GitHub Assistant")
console = Console()


@app.command()
def trending(
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter by programming language"),
    since: str = typer.Option("daily", "--since", "-s", help="Time range: daily, weekly, monthly"),
    limit: int = typer.Option(10, "--limit", help="Number of repos to show"),
):
    """Get trending GitHub repositories"""
    console.print("[bold blue]🔍 Fetching trending repositories...[/bold blue]")

    try:
        tool = GitHubTrendingTool()
        repos = tool.get_trending_repos(language=language, since=since, limit=limit)

        if not repos:
            console.print("[yellow]No trending repositories found.[/yellow]")
            return

        # Create table
        table = Table(title=f"🔥 Trending Repositories ({since})")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Repository", style="magenta", width=30)
        table.add_column("Stars", style="green", width=10)
        table.add_column("Language", style="yellow", width=12)
        table.add_column("Description", style="white", width=50)

        for i, repo in enumerate(repos, 1):
            desc = repo['description'][:47] + "..." if len(repo['description']) > 50 else repo['description']
            table.add_row(
                str(i),
                repo['name'],
                f"⭐ {repo['stars']}",
                repo['language'] or "N/A",
                desc
            )

        console.print(table)

        # Show summary
        summary = tool.get_trending_summary(repos)
        console.print("\n[bold]Summary:[/bold]")
        console.print(Markdown(summary))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def prs(
    repo: str = typer.Argument(..., help="Repository full name (owner/repo)"),
    valuable: bool = typer.Option(False, "--valuable", "-v", help="Show only valuable PRs"),
    limit: int = typer.Option(10, "--limit", help="Number of PRs to show"),
):
    """Get today's pull requests for a repository"""
    console.print(f"[bold blue]🔍 Fetching PRs for {repo}...[/bold blue]")

    try:
        tool = GitHubPRTool()

        if valuable:
            prs = tool.get_valuable_prs(repo, limit=limit)
            title = f"💎 Most Valuable PRs - {repo}"
        else:
            prs = tool.get_today_prs(repo, limit=limit)
            title = f"📝 Today's PRs - {repo}"

        if not prs or "error" in prs[0]:
            console.print(f"[yellow]No PRs found for {repo} today.[/yellow]")
            return

        # Create table
        table = Table(title=title)
        table.add_column("#", style="cyan", width=6)
        table.add_column("Title", style="magenta", width=40)
        table.add_column("Author", style="green", width=15)
        table.add_column("State", style="yellow", width=8)
        table.add_column("Comments", style="blue", width=10)
        if valuable:
            table.add_column("Score", style="red", width=8)

        for i, pr in enumerate(prs, 1):
            title_text = pr['title'][:37] + "..." if len(pr['title']) > 40 else pr['title']
            row = [
                f"#{pr['number']}",
                title_text,
                pr['author'],
                pr['state'],
                str(pr['comments'])
            ]
            if valuable:
                row.append(str(pr.get('value_score', 0)))
            table.add_row(*row)

        console.print(table)

        # Show URLs
        console.print("\n[bold]PR URLs:[/bold]")
        for pr in prs[:5]:
            console.print(f"  • [#{pr['number']}]({pr['url']}) - {pr['title'][:50]}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def analyze_pr(
    repo: str = typer.Argument(..., help="Repository full name (owner/repo)"),
    pr_number: int = typer.Argument(..., help="PR number"),
):
    """Analyze a specific pull request in detail"""
    console.print(f"[bold blue]🔍 Analyzing PR #{pr_number} in {repo}...[/bold blue]")

    try:
        tool = GitHubPRTool()
        analysis = tool.analyze_pr(repo, pr_number)

        if "error" in analysis:
            console.print(f"[red]Error: {analysis['error']}[/red]")
            return

        # Display analysis
        info = f"""
**PR #{analysis['number']}**: {analysis['title']}

**State**: {analysis['state']}
**Author**: {analysis['author']}
**Value Score**: {analysis['value_score']}

**Statistics**:
- Files Changed: {analysis['files_changed']}
- Additions: +{analysis['additions']}
- Deletions: -{analysis['deletions']}
- Comments: {analysis['comments']}
- Review Comments: {analysis['review_comments']}

**Reviews**:
- Total: {analysis['review_summary']['total']}
- Approved: {analysis['review_summary']['approved']}
- Changes Requested: {analysis['review_summary']['changes_requested']}

**Maintainer Participated**: {'Yes' if analysis['maintainer_participated'] else 'No'}

**URL**: {analysis['url']}
        """

        console.print(Panel(Markdown(info), title="PR Analysis", border_style="green"))

        # Show file changes
        if analysis.get('file_details'):
            console.print("\n[bold]Files Changed:[/bold]")
            file_table = Table()
            file_table.add_column("File", style="cyan")
            file_table.add_column("Status", style="yellow")
            file_table.add_column("Changes", style="green")

            for file in analysis['file_details'][:10]:
                file_table.add_row(
                    file['filename'],
                    file['status'],
                    f"+{file['additions']} -{file['deletions']}"
                )
            console.print(file_table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def create_issue(
    repo: str = typer.Argument(..., help="Repository full name (owner/repo)"),
    text: str = typer.Argument(..., help="Issue description in natural language"),
    assignees: Optional[str] = typer.Option(None, "--assignees", help="Comma-separated list of assignees"),
    labels: Optional[str] = typer.Option(None, "--labels", help="Comma-separated list of labels"),
):
    """Create a GitHub issue from natural language"""
    console.print(f"[bold blue]📝 Creating issue in {repo}...[/bold blue]")

    try:
        tool = GitHubIssueTool()

        assignee_list = [a.strip() for a in assignees.split(",")] if assignees else None
        label_list = [l.strip() for l in labels.split(",")] if labels else None

        result = tool.create_issue_from_text(
            repo,
            text,
            assignees=assignee_list,
            labels=label_list
        )

        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
            return

        info = f"""
**Issue Created Successfully!**

**#{result['number']}**: {result['title']}
**URL**: {result['url']}
**Labels**: {', '.join(result['labels'])}

**Similar Issues Found**: {len(result.get('similar_issues', []))}
        """

        console.print(Panel(Markdown(info), title="Issue Created", border_style="green"))

        if result.get('similar_issues'):
            console.print("\n[yellow]⚠️  Similar issues:[/yellow]")
            for similar in result['similar_issues'][:3]:
                console.print(f"  • [#{similar['number']}]({similar['url']}) - {similar['title']}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def chat(
    message: str = typer.Argument(..., help="Your question or command"),
):
    """Chat with HubMind agent using natural language"""
    console.print("[bold blue]🤖 HubMind Agent is thinking...[/bold blue]")

    try:
        agent = HubMindAgent()
        response = agent.chat(message)

        console.print("\n[bold green]HubMind:[/bold green]")
        console.print(Panel(Markdown(response), border_style="blue"))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def ask(
    repo: str = typer.Argument(..., help="Repository full name (owner/repo)"),
    question: str = typer.Argument(..., help="Your question about the repository"),
):
    """Ask questions about a repository"""
    console.print(f"[bold blue]💬 Answering question about {repo}...[/bold blue]")

    try:
        qa_agent = HubMindQAAgent()
        result = qa_agent.answer_repo_question(repo, question)

        console.print("\n[bold green]Answer:[/bold green]")
        console.print(Panel(Markdown(result['answer']), border_style="green"))

        if result.get('sources'):
            console.print("\n[bold]Sources:[/bold]")
            for source in result['sources']:
                console.print(f"  • {source}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def health(
    repo: str = typer.Argument(..., help="Repository full name (owner/repo)"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
):
    """Get repository health metrics"""
    console.print(f"[bold blue]📊 Analyzing health of {repo}...[/bold blue]")

    try:
        dashboard = DeveloperDashboard()
        health = dashboard.get_repo_health(repo, days=days)

        if "error" in health:
            console.print(f"[red]Error: {health['error']}[/red]")
            return

        info = f"""
**Repository Health Report** ({health['period_days']} days)

**Metrics**:
- Average Issue Response Time: {health['avg_issue_response_hours']} hours
- PR Merge Rate: {health['pr_merge_rate']}%
- Active Contributors: {health['active_contributors']}
- Commits per Day: {health['commits_per_day']}
- Total Commits: {health['total_commits']}

**Current Status**:
- Open Issues: {health['open_issues']}
- Stars: {health['stars']}
- Forks: {health['forks']}

**Top Contributors**: {', '.join(health['contributor_list'][:5])}
        """

        console.print(Panel(Markdown(info), title="Health Report", border_style="cyan"))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def watch(
    repos: str = typer.Argument(..., help="Comma-separated list of repositories"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours to look back"),
):
    """Watch activity for multiple repositories"""
    repo_list = [r.strip() for r in repos.split(",")]
    console.print(f"[bold blue]👀 Watching {len(repo_list)} repositories...[/bold blue]")

    try:
        dashboard = DeveloperDashboard()
        activities = dashboard.get_watched_repos_activity(repo_list, hours=hours)

        table = Table(title=f"Repository Activity (last {hours} hours)")
        table.add_column("Repository", style="magenta", width=30)
        table.add_column("New PRs", style="green", width=10)
        table.add_column("Updated PRs", style="blue", width=12)
        table.add_column("New Issues", style="yellow", width=12)
        table.add_column("Updated Issues", style="cyan", width=14)
        table.add_column("Commits", style="red", width=10)

        for activity in activities:
            if "error" not in activity:
                table.add_row(
                    activity['repo'],
                    str(activity['new_prs']),
                    str(activity['updated_prs']),
                    str(activity['new_issues']),
                    str(activity['updated_issues']),
                    str(activity['commits'])
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def interactive():
    """Start interactive chat mode"""
    console.print("[bold green]🤖 HubMind Interactive Mode[/bold green]")
    console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")

    try:
        agent = HubMindAgent()
        chat_history = []

        while True:
            try:
                user_input = console.input("[bold cyan]You:[/bold cyan] ")

                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break

                if not user_input.strip():
                    continue

                response = agent.chat(user_input, chat_history)
                console.print(f"\n[bold green]HubMind:[/bold green]")
                console.print(Panel(Markdown(response), border_style="blue"))
                console.print()  # Empty line

                # Update chat history
                chat_history.append(("human", user_input))
                chat_history.append(("ai", response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")

    except Exception as e:
        console.print(f"[red]Error initializing agent: {str(e)}[/red]")


if __name__ == "__main__":
    app()
