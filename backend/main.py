"""
HubMind Backend - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(Path(__file__).parent / '.env')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.hubmind_agent import HubMindAgent
from src.agents.qa_agent import HubMindQAAgent
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.utils.dashboard import DeveloperDashboard
from config import Config

app = FastAPI(
    title="HubMind API",
    description="GitHub Intelligent Assistant API",
    version="0.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    chat_history: List[Dict[str, str]]

class TrendingRequest(BaseModel):
    language: Optional[str] = None
    since: str = "daily"
    limit: int = 10

class PRRequest(BaseModel):
    repo: str
    limit: int = 10
    valuable: bool = False

class AnalyzePRRequest(BaseModel):
    repo: str
    pr_number: int

class CreateIssueRequest(BaseModel):
    repo: str
    text: str
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None

class QARequest(BaseModel):
    repo: str
    question: str

class HealthRequest(BaseModel):
    repo: str
    days: int = 30

# Initialize agents and tools (lazy loading)
_agent: Optional[HubMindAgent] = None
_qa_agent: Optional[HubMindQAAgent] = None
_trending_tool: Optional[GitHubTrendingTool] = None
_pr_tool: Optional[GitHubPRTool] = None
_issue_tool: Optional[GitHubIssueTool] = None
_dashboard: Optional[DeveloperDashboard] = None

def get_agent() -> HubMindAgent:
    global _agent
    if _agent is None:
        _agent = HubMindAgent()
    return _agent

def get_qa_agent() -> HubMindQAAgent:
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = HubMindQAAgent()
    return _qa_agent

def get_trending_tool() -> GitHubTrendingTool:
    global _trending_tool
    if _trending_tool is None:
        _trending_tool = GitHubTrendingTool()
    return _trending_tool

def get_pr_tool() -> GitHubPRTool:
    global _pr_tool
    if _pr_tool is None:
        _pr_tool = GitHubPRTool()
    return _pr_tool

def get_issue_tool() -> GitHubIssueTool:
    global _issue_tool
    if _issue_tool is None:
        _issue_tool = GitHubIssueTool()
    return _issue_tool

def get_dashboard() -> DeveloperDashboard:
    global _dashboard
    if _dashboard is None:
        _dashboard = DeveloperDashboard()
    return _dashboard

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "HubMind API",
        "version": "0.2.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "trending": "/api/trending",
            "prs": "/api/prs",
            "analyze_pr": "/api/analyze-pr",
            "create_issue": "/api/create-issue",
            "qa": "/api/qa",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "HubMind API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with HubMind agent"""
    try:
        agent = get_agent()

        # Run agent.chat in executor to avoid blocking the event loop
        # This prevents BrokenPipeError when client disconnects
        import asyncio
        import concurrent.futures

        def run_agent():
            try:
                return agent.chat(request.message, request.chat_history)
            except (BrokenPipeError, ConnectionError, OSError) as e:
                # Handle connection errors gracefully
                return f"连接错误: {str(e)}。请重试。"
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"Agent execution error: {error_detail[:500]}")
                return f"处理请求时出错: {str(e)}"

        # Use ThreadPoolExecutor to run blocking code
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(executor, run_agent)

        # Update chat history
        chat_history = request.chat_history or []
        chat_history.append({"role": "user", "content": request.message})
        chat_history.append({"role": "assistant", "content": response})

        return ChatResponse(response=response, chat_history=chat_history)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"API error: {error_detail[:500]}")
        # Return error in response instead of raising exception
        chat_history = request.chat_history or [] if 'request' in locals() else []
        chat_history.append({"role": "user", "content": request.message if 'request' in locals() else ""})
        chat_history.append({"role": "assistant", "content": f"服务器错误: {str(e)}"})
        return ChatResponse(response=f"服务器错误: {str(e)}", chat_history=chat_history)

@app.post("/api/trending")
async def get_trending(request: TrendingRequest):
    """Get trending repositories"""
    try:
        tool = get_trending_tool()
        repos = tool.get_trending_repos(
            language=request.language,
            since=request.since,
            limit=request.limit
        )
        summary = tool.get_trending_summary(repos)
        return {
            "repos": repos,
            "summary": summary,
            "count": len(repos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prs")
async def get_prs(request: PRRequest):
    """Get pull requests for a repository"""
    try:
        tool = get_pr_tool()
        if request.valuable:
            prs = tool.get_valuable_prs(request.repo, limit=request.limit)
        else:
            prs = tool.get_today_prs(request.repo, limit=request.limit)
        return {
            "repo": request.repo,
            "prs": prs,
            "count": len(prs),
            "valuable": request.valuable
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-pr")
async def analyze_pr(request: AnalyzePRRequest):
    """Analyze a specific pull request"""
    try:
        tool = get_pr_tool()
        analysis = tool.analyze_pr(request.repo, request.pr_number)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-issue")
async def create_issue(request: CreateIssueRequest):
    """Create a GitHub issue"""
    try:
        tool = get_issue_tool()
        result = tool.create_issue_from_text(
            request.repo,
            request.text,
            assignees=request.assignees,
            labels=request.labels
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa")
async def ask_question(request: QARequest):
    """Ask a question about a repository"""
    try:
        qa_agent = get_qa_agent()
        result = qa_agent.answer_repo_question(request.repo, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/health-repo")
async def get_repo_health(request: HealthRequest):
    """Get repository health metrics"""
    try:
        dashboard = get_dashboard()
        health = dashboard.get_repo_health(request.repo, days=request.days)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GitHub Browser API
class GitHubRepoRequest(BaseModel):
    repo: str

class GitHubFilesRequest(BaseModel):
    repo: str
    path: str = ""

@app.post("/api/github/repo-info")
async def get_repo_info(request: GitHubRepoRequest):
    """Get GitHub repository information"""
    try:
        from github import Github
        github = Github(Config.GITHUB_TOKEN)
        repo = github.get_repo(request.repo)

        return {
            "id": repo.id,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "language": repo.language,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "watchers_count": repo.watchers_count,
            "open_issues_count": repo.open_issues_count,
            "default_branch": repo.default_branch,
            "size": repo.size,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "license": {
                "name": repo.license.name if repo.license else None,
                "spdx_id": repo.license.spdx_id if repo.license else None,
            } if repo.license else None,
            "topics": list(repo.get_topics()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/github/repo-files")
async def get_repo_files(request: GitHubFilesRequest):
    """Get repository files and directories"""
    try:
        from github import Github
        github = Github(Config.GITHUB_TOKEN)
        repo = github.get_repo(request.repo)

        contents = repo.get_contents(request.path) if request.path else repo.get_contents("")

        # Handle single file vs list
        if not isinstance(contents, list):
            contents = [contents]

        files = []
        for content in contents:
            files.append({
                "name": content.name,
                "path": content.path,
                "type": content.type,  # 'file' or 'dir'
                "size": content.size if hasattr(content, 'size') else None,
                "html_url": content.html_url,
                "download_url": content.download_url,
            })

        # Sort: directories first, then files
        files.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))

        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/github/readme")
async def get_readme(request: GitHubRepoRequest):
    """Get repository README content"""
    try:
        from github import Github
        import base64
        github = Github(Config.GITHUB_TOKEN)
        repo = github.get_repo(request.repo)

        try:
            readme = repo.get_readme()
            # Decode base64 content
            content = base64.b64decode(readme.content).decode('utf-8')
            return {
                "content": content,
                "name": readme.name,
                "path": readme.path,
                "html_url": readme.html_url,
            }
        except Exception as e:
            # README not found
            return {
                "content": "# README not found\n\nThis repository does not have a README file.",
                "name": "README.md",
                "path": "README.md",
                "html_url": None,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
