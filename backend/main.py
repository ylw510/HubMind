"""
HubMind Backend - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env（override=True 避免被 shell 已有空 DATABASE_URL 覆盖）
load_dotenv(Path(__file__).resolve().parent / '.env', override=True)

# Add backend and project root to path
_backend_dir = Path(__file__).parent
_root_dir = _backend_dir.parent
sys.path.insert(0, str(_backend_dir))
sys.path.append(str(_root_dir))

from src.agents.hubmind_agent import HubMindAgent
from src.agents.qa_agent import HubMindQAAgent
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.utils.dashboard import DeveloperDashboard
from config import Config

# Auth and database (backend-local)
from database import init_db, get_db, User, UserSettings, SessionLocal
from auth import get_password_hash, verify_password, create_access_token, decode_access_token  # noqa: E501
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="HubMind API",
    description="GitHub Intelligent Assistant API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware（允许本地开发任意端口，避免 Vite 使用 3001/3002 时被拦截）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
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


# Auth & Settings models
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SettingsUpdateRequest(BaseModel):
    github_token: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class SettingsResponse(BaseModel):
    github_token: str  # masked in response: show only last 4 chars or "***"
    llm_provider: str
    llm_api_key: str  # masked


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


def get_user_settings(db: Session, user_id: int) -> Optional[UserSettings]:
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return current user if valid Bearer token present, else None."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    user = db.query(User).filter(User.id == uid).first()
    return user


def get_current_user_required(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    """Require authenticated user; raise 401 if not."""
    if user is None:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user


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


# ----- Auth & Settings -----
@app.post("/api/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        if not data.username or not data.username.strip():
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="密码至少 6 位")
        username = data.username.strip()
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user = User(
            username=username,
            password_hash=get_password_hash(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@app.post("/api/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login and return JWT."""
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}


@app.get("/api/me")
async def me(user: User = Depends(get_current_user_required)):
    """Get current user info."""
    return {"id": user.id, "username": user.username}


@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    """Get current user's settings (tokens masked)."""
    settings = get_user_settings(db, user.id)
    if not settings:
        return SettingsResponse(github_token="", llm_provider="deepseek", llm_api_key="")
    def mask(s: str) -> str:
        if not s or len(s) <= 4:
            return "***" if s else ""
        return "***" + s[-4:]
    return SettingsResponse(
        github_token=mask(settings.github_token or ""),
        llm_provider=settings.llm_provider or "deepseek",
        llm_api_key=mask(settings.llm_api_key or ""),
    )


@app.put("/api/settings")
async def update_settings(
    data: SettingsUpdateRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """Update current user's LLM and GitHub settings."""
    settings = get_user_settings(db, user.id)
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    if data.github_token is not None:
        settings.github_token = data.github_token
    if data.llm_provider is not None:
        settings.llm_provider = data.llm_provider
    if data.llm_api_key is not None:
        settings.llm_api_key = data.llm_api_key
    db.commit()
    return {"ok": True}


@app.put("/api/password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """修改当前用户密码。"""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"ok": True}


def _agent_for_user(db: Session, user: User) -> Optional[HubMindAgent]:
    """Create HubMindAgent with user's settings if they have tokens set."""
    settings = get_user_settings(db, user.id)
    if not settings or (not settings.github_token and not settings.llm_api_key):
        return None
    return HubMindAgent(
        provider=settings.llm_provider or Config.LLM_PROVIDER,
        github_token=settings.github_token or None,
        llm_api_key=settings.llm_api_key or None,
    )


def _qa_agent_for_user(db: Session, user: User) -> Optional[HubMindQAAgent]:
    settings = get_user_settings(db, user.id)
    if not settings or (not settings.github_token and not settings.llm_api_key):
        return None
    return HubMindQAAgent(
        provider=settings.llm_provider or Config.LLM_PROVIDER,
        github_token=settings.github_token or None,
        llm_api_key=settings.llm_api_key or None,
    )


def _github_for_user(db: Session, user: User):
    """Return PyGithub instance for user's token, or None."""
    settings = get_user_settings(db, user.id)
    if not settings or not settings.github_token:
        return None
    from github import Github
    return Github(settings.github_token)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Chat with HubMind agent"""
    try:
        agent = _agent_for_user(db, user) if user else None
        if agent is None:
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
async def get_trending(
    request: TrendingRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get trending repositories"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            tool = GitHubTrendingTool(github_token=token) if token else get_trending_tool()
        else:
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
async def get_prs(
    request: PRRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get pull requests for a repository"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            tool = GitHubPRTool(github_token=token) if token else get_pr_tool()
        else:
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
async def analyze_pr(
    request: AnalyzePRRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Analyze a specific pull request"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            tool = GitHubPRTool(github_token=token) if token else get_pr_tool()
        else:
            tool = get_pr_tool()
        analysis = tool.analyze_pr(request.repo, request.pr_number)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-issue")
async def create_issue(
    request: CreateIssueRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a GitHub issue"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            tool = GitHubIssueTool(github_token=token) if token else get_issue_tool()
        else:
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
async def ask_question(
    request: QARequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Ask a question about a repository"""
    try:
        qa_agent = _qa_agent_for_user(db, user) if user else None
        if qa_agent is None:
            qa_agent = get_qa_agent()
        result = qa_agent.answer_repo_question(request.repo, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/health-repo")
async def get_repo_health(
    request: HealthRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get repository health metrics"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            dashboard = DeveloperDashboard(github_token=token) if token else get_dashboard()
        else:
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
async def get_repo_info(
    request: GitHubRepoRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get GitHub repository information"""
    try:
        from github import Github
        github = _github_for_user(db, user) if user else None
        if github is None:
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
async def get_repo_files(
    request: GitHubFilesRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get repository files and directories"""
    try:
        from github import Github
        github = _github_for_user(db, user) if user else None
        if github is None:
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
async def get_readme(
    request: GitHubRepoRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get repository README content"""
    try:
        from github import Github
        import base64
        github = _github_for_user(db, user) if user else None
        if github is None:
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
