"""
HubMind Backend - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import asyncio

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
from src.utils.logger import get_logger
from config import Config

# Setup logger
logger = get_logger(__name__)

# Auth and database (backend-local)
from database import init_db, get_db, User, UserSettings, ChatSession, ChatMessage, SessionLocal
from auth import get_password_hash, verify_password, create_access_token, decode_access_token  # noqa: E501
from sqlalchemy.orm import Session
from sqlalchemy import desc


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HubMind API server...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down HubMind API server...")


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
    repo: Optional[str] = None  # 仓库名称，格式: owner/repo
    session_id: Optional[int] = None  # 对话会话 ID

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

class ParseIssueRequest(BaseModel):
    repo: str
    text: str

class UpdateIssueDraftRequest(BaseModel):
    repo: str
    title: str
    body: str
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None

# Chat Session Models
class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New chat"
    repo: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    repo: Optional[str] = None

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
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class SettingsResponse(BaseModel):
    github_token: str
    llm_provider: str
    llm_api_key: str
    llm_base_url: str = ""
    llm_model: str = ""


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
        return SettingsResponse(github_token="", llm_provider="deepseek", llm_api_key="", llm_base_url="", llm_model="")
    def mask(s: str) -> str:
        if not s or len(s) <= 4:
            return "***" if s else ""
        return "***" + s[-4:]
    return SettingsResponse(
        github_token=mask(settings.github_token or ""),
        llm_provider=settings.llm_provider or "deepseek",
        llm_api_key=mask(settings.llm_api_key or ""),
        llm_base_url=getattr(settings, "llm_base_url", None) or "",
        llm_model=getattr(settings, "llm_model", None) or "",
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
    if data.llm_base_url is not None:
        settings.llm_base_url = data.llm_base_url
    if data.llm_model is not None:
        settings.llm_model = data.llm_model
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
        llm_base_url=settings.llm_base_url or None,
        llm_model=settings.llm_model or None,
    )


def _qa_agent_for_user(db: Session, user: User) -> Optional[HubMindQAAgent]:
    settings = get_user_settings(db, user.id)
    if not settings or (not settings.github_token and not settings.llm_api_key):
        return None
    return HubMindQAAgent(
        provider=settings.llm_provider or Config.LLM_PROVIDER,
        github_token=settings.github_token or None,
        llm_api_key=settings.llm_api_key or None,
        llm_base_url=settings.llm_base_url or None,
        llm_model=settings.llm_model or None,
    )


def _github_for_user(db: Session, user: User):
    """Return PyGithub instance for user's token, or None."""
    settings = get_user_settings(db, user.id)
    if not settings or not settings.github_token:
        return None
    from github import Github
    return Github(settings.github_token)

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Chat with HubMind agent (streaming)"""
    try:
        agent = _agent_for_user(db, user) if user else None
        if agent is None:
            agent = get_agent()

        # 如果指定了仓库，在消息中添加仓库上下文
        message = request.message
        if request.repo:
            message = f"[仓库: {request.repo}]\n{message}"

        async def generate_stream():
            """Generate streaming response"""
            full_response = ""
            chunk_count = 0
            try:
                logger.debug(f"[STREAM] Starting stream for message: {message[:50]}...")
                logger.debug(f"[STREAM] Agent type: {type(agent)}")

                # Run synchronous stream in executor to avoid blocking
                import concurrent.futures
                import asyncio
                loop = asyncio.get_event_loop()
                logger.debug(f"[STREAM] Event loop: {loop}")

                # Create a queue to pass chunks from sync generator to async generator
                queue = asyncio.Queue(maxsize=100)  # Limit queue size to prevent memory issues
                stream_error = None
                chunks_produced = 0
                chunks_queued = 0

                def run_sync_stream():
                    """Run synchronous stream in thread"""
                    nonlocal stream_error, chunks_produced, chunks_queued
                    try:
                        logger.debug("[SYNC_STREAM] Starting sync stream in thread...")
                        logger.debug(f"[SYNC_STREAM] Message: {message[:50]}...")
                        logger.debug(f"[SYNC_STREAM] Chat history: {len(request.chat_history) if request.chat_history else 0} messages")

                        chunk_gen = agent.chat_stream(message, request.chat_history)
                        logger.debug(f"[SYNC_STREAM] Generator created: {type(chunk_gen)}")

                        for chunk in chunk_gen:
                            chunks_produced += 1
                            logger.debug(f"[SYNC_STREAM] Got chunk #{chunks_produced}, type: {type(chunk)}, length: {len(str(chunk)) if chunk else 0}")

                            # Put chunk in queue using thread-safe method
                            try:
                                # Use call_soon_threadsafe with a callback that puts in queue
                                def put_chunk(chunk_val):
                                    nonlocal chunks_queued
                                    try:
                                        queue.put_nowait(chunk_val)
                                        chunks_queued += 1
                                        # Only log every 10th chunk to reduce noise
                                        if chunks_queued % 10 == 0:
                                            logger.debug(f"[SYNC_STREAM] {chunks_queued} chunks queued")
                                    except asyncio.QueueFull:
                                        logger.warning(f"[SYNC_STREAM] Queue full, dropping chunk #{chunks_produced}")

                                loop.call_soon_threadsafe(put_chunk, chunk)
                                logger.debug(f"[SYNC_STREAM] Scheduled chunk #{chunks_produced} to be queued")
                            except Exception as put_error:
                                logger.error(f"[SYNC_STREAM] Error putting chunk in queue: {str(put_error)}")
                                import traceback
                                logger.error(f"[SYNC_STREAM] Traceback: {traceback.format_exc()}")
                                break

                        # Signal done
                        logger.debug(f"[SYNC_STREAM] Stream finished. Total chunks produced: {chunks_produced}, queued: {chunks_queued}")
                        loop.call_soon_threadsafe(lambda: queue.put_nowait(None))
                        logger.debug("[SYNC_STREAM] Done signal sent to queue")
                    except Exception as e:
                        logger.error(f"[SYNC_STREAM] Error in sync stream: {str(e)}")
                        import traceback
                        logger.error(f"[SYNC_STREAM] Traceback: {traceback.format_exc()}")
                        stream_error = str(e)
                        try:
                            loop.call_soon_threadsafe(lambda: queue.put_nowait(None))
                        except Exception as final_error:
                            logger.error(f"[SYNC_STREAM] Error sending done signal: {str(final_error)}")

                # Start sync stream in executor
                logger.debug("[STREAM] Creating ThreadPoolExecutor...")
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                logger.debug("[STREAM] Submitting run_sync_stream to executor...")
                future = executor.submit(run_sync_stream)
                logger.debug("[STREAM] Executor task submitted, waiting for chunks...")

                # Consume chunks from queue with timeout
                try:
                    while True:
                        try:
                            logger.debug(f"[STREAM] Waiting for chunk from queue (current count: {chunk_count})...")
                            # Wait for chunk with timeout
                            chunk = await asyncio.wait_for(queue.get(), timeout=300.0)  # 5 minute timeout
                            logger.debug(f"[STREAM] Got chunk from queue: {chunk is not None}, type: {type(chunk)}")

                            if chunk is None:  # Done signal
                                logger.debug("[STREAM] Received done signal from queue")
                                break

                            chunk_count += 1
                            logger.debug(f"[STREAM] Processing chunk #{chunk_count}, length: {len(str(chunk)) if chunk else 0}")

                            if chunk:
                                full_response += chunk
                                logger.debug(f"[STREAM] Full response length: {len(full_response)}")

                                # Send chunk as JSON (Server-Sent Events format)
                                chunk_data = json.dumps({'chunk': chunk, 'done': False}, ensure_ascii=False)
                                logger.debug(f"[STREAM] Sending chunk data: {chunk_data[:100]}...")
                                yield f"data: {chunk_data}\n\n"
                                # Only log every 20th chunk to reduce noise
                                if chunk_count % 20 == 0:
                                    logger.debug(f"[STREAM] {chunk_count} chunks sent to client")
                        except asyncio.TimeoutError:
                            logger.error("[STREAM] Timeout waiting for stream chunks")
                            break
                        except Exception as chunk_error:
                            logger.error(f"[STREAM] Error processing chunk: {str(chunk_error)}")
                            import traceback
                            logger.error(f"[STREAM] Traceback: {traceback.format_exc()}")
                            break
                finally:
                    logger.debug(f"[STREAM] Exiting chunk consumption loop. Total chunks: {chunk_count}")
                    # Wait for executor to finish (with timeout)
                    try:
                        logger.debug("[STREAM] Waiting for executor to finish...")
                        future.result(timeout=10)
                        logger.debug("[STREAM] Executor finished successfully")
                    except concurrent.futures.TimeoutError:
                        logger.warning("[STREAM] Executor did not finish in time")
                    except Exception as e:
                        logger.error(f"[STREAM] Error waiting for executor: {str(e)}")
                        import traceback
                        logger.error(f"[STREAM] Traceback: {traceback.format_exc()}")
                    finally:
                        logger.debug("[STREAM] Shutting down executor...")
                        executor.shutdown(wait=False)
                        logger.debug("[STREAM] Executor shut down")

                # Check for stream errors
                if stream_error:
                    logger.error(f"[STREAM] Stream error occurred: {stream_error}")
                    error_chunk = f'\n\n错误: {stream_error}'
                    error_data = json.dumps({'chunk': error_chunk, 'done': False}, ensure_ascii=False)
                    yield f"data: {error_data}\n\n"

                logger.debug(f"[STREAM] Stream completed: {chunk_count} chunks received, {len(full_response)} chars total")
                logger.debug(f"[STREAM] Chunks produced: {chunks_produced}, queued: {chunks_queued}")
                if chunk_count == 0:
                    logger.warning("[STREAM] No chunks received from agent.chat_stream()")
                if len(full_response) == 0:
                    logger.warning("[STREAM] No content in full_response after streaming")
                # Send final message
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'full_response': full_response}, ensure_ascii=False)}\n\n"

                # Save to database if user is logged in and session_id is provided
                # Run database operations in executor to avoid blocking
                if user and request.session_id is not None:
                    try:
                        import concurrent.futures
                        loop = asyncio.get_event_loop()

                        def save_messages():
                            try:
                                session = db.query(ChatSession).filter(
                                    ChatSession.id == request.session_id,
                                    ChatSession.user_id == user.id
                                ).first()
                                if session:
                                    # Add new messages to database
                                    user_msg = ChatMessage(
                                        session_id=session.id,
                                        role="user",
                                        content=request.message
                                    )
                                    assistant_msg = ChatMessage(
                                        session_id=session.id,
                                        role="assistant",
                                        content=full_response
                                    )
                                    db.add(user_msg)
                                    db.add(assistant_msg)
                                    session.updated_at = datetime.utcnow()
                                    db.commit()
                            except Exception as e:
                                logger.error(f"Error saving chat messages: {str(e)}")
                                db.rollback()

                        # Run in executor to avoid blocking
                        await loop.run_in_executor(None, save_messages)
                    except Exception as e:
                        logger.error(f"Error saving chat messages: {str(e)}")

            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
                error_msg = f"服务器错误: {str(e)}"
                yield f"data: {json.dumps({'chunk': error_msg, 'done': True, 'error': True}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"API error: {error_detail[:500]}")
        logger.debug(f"Full traceback: {error_detail}")
        # Return error as stream
        async def error_stream():
            error_msg = f"服务器错误: {str(e)}"
            yield f"data: {json.dumps({'chunk': error_msg, 'done': True, 'error': True}, ensure_ascii=False)}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

@app.post("/api/trending")
async def get_trending(
    request: TrendingRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get trending repositories（抓取 GitHub Trending 页 + AI 总结）"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            if settings:
                tool = GitHubTrendingTool(
                    github_token=settings.github_token or None,
                    llm_provider=settings.llm_provider or None,
                    llm_api_key=settings.llm_api_key or None,
                )
            else:
                tool = get_trending_tool()
        else:
            tool = get_trending_tool()
        repos = tool.get_trending_repos(
            language=request.language,
            since=request.since,
            limit=request.limit,
        )
        summary = tool.get_trending_summary(
            repos,
            language=request.language,
            since=request.since,
            use_llm=True,
        )
        return {
            "repos": repos,
            "summary": summary,
            "count": len(repos),
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

@app.post("/api/parse-issue")
async def parse_issue(
    request: ParseIssueRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Parse natural language text into issue draft (title, body, suggested labels)"""
    try:
        if user:
            settings = get_user_settings(db, user.id)
            token = (settings.github_token or "") if settings else ""
            tool = GitHubIssueTool(github_token=token) if token else get_issue_tool()
        else:
            tool = get_issue_tool()

        # Parse text to extract title and body
        parsed = tool._parse_issue_text(request.text)
        classification = tool.classify_issue(request.text)

        # Get similar issues
        try:
            from github import Github
            github = _github_for_user(db, user) if user else None
            if github is None:
                github = Github(Config.GITHUB_TOKEN)
            repo = github.get_repo(request.repo)
            similar_issues = tool._find_similar_issues(repo, parsed["title"])
        except:
            similar_issues = []

        return {
            "title": parsed["title"],
            "body": parsed["body"],
            "suggested_labels": parsed.get("suggested_labels", []),
            "issue_type": classification.get("type", "question"),
            "priority": classification.get("priority", "medium"),
            "similar_issues": similar_issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/github/repo-labels")
async def get_repo_labels(
    repo: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get available labels for a repository"""
    try:
        from github import Github
        github = _github_for_user(db, user) if user else None
        if github is None:
            github = Github(Config.GITHUB_TOKEN)
        repo_obj = github.get_repo(repo)

        labels = []
        for label in repo_obj.get_labels():
            labels.append({
                "name": label.name,
                "color": label.color,
                "description": label.description or "",
            })

        return {"labels": labels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/github/repo-collaborators")
async def get_repo_collaborators(
    repo: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get collaborators for a repository"""
    try:
        from github import Github
        github = _github_for_user(db, user) if user else None
        if github is None:
            github = Github(Config.GITHUB_TOKEN)
        repo_obj = github.get_repo(repo)

        collaborators = []
        for collab in repo_obj.get_collaborators():
            collaborators.append({
                "login": collab.login,
                "avatar_url": collab.avatar_url,
            })

        return {"collaborators": collaborators}
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

@app.post("/api/create-issue-draft")
async def create_issue_draft(
    request: UpdateIssueDraftRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a GitHub issue from draft (title, body, etc.)"""
    try:
        from github import Github
        github = _github_for_user(db, user) if user else None
        if github is None:
            github = Github(Config.GITHUB_TOKEN)
        repo = github.get_repo(request.repo)

        # Create issue
        issue = repo.create_issue(
            title=request.title,
            body=request.body,
            assignees=request.assignees or [],
            labels=request.labels or []
        )

        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "url": issue.html_url,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
        }
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

@app.get("/api/github/user-repos")
async def get_user_repos(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get repositories owned by the current user"""
    try:
        from github import Github
        from github.GithubException import GithubException

        # 优先使用用户的 GitHub token
        github = None
        if user:
            github = _github_for_user(db, user)
            if github:
                logger.info(f"Using user's GitHub token for user: {user.username}")
            else:
                logger.warning(f"User {user.username} has no GitHub token configured")

        # 如果用户没有 token，尝试使用全局配置的 token
        if github is None:
            if Config.GITHUB_TOKEN:
                github = Github(Config.GITHUB_TOKEN)
                logger.info("Using global GitHub token from config")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="未配置 GitHub Token。请在设置页面配置你的 GitHub Token。"
                )

        # 获取当前认证用户
        try:
            authenticated_user = github.get_user()
            logger.info(f"Authenticated as: {authenticated_user.login}")
        except GithubException as e:
            logger.error(f"GitHub API error: status={e.status}, message={e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}")
            if e.status == 401:
                raise HTTPException(
                    status_code=401,
                    detail="GitHub Token 无效或已过期。请在设置页面更新你的 GitHub Token。"
                )
            elif e.status == 404:
                raise HTTPException(
                    status_code=404,
                    detail="GitHub API 返回 404。请检查 Token 是否正确。"
                )
            raise HTTPException(
                status_code=500,
                detail=f"GitHub API 错误: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            )

        # 获取用户拥有的仓库（包括私有仓库）
        try:
            repos = authenticated_user.get_repos(type='all', sort='updated', direction='desc')
            logger.info(f"Successfully fetched repos iterator for user: {authenticated_user.login}")
        except GithubException as e:
            logger.error(f"Error fetching repos: status={e.status}, message={e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}")
            if e.status == 403:
                raise HTTPException(
                    status_code=403,
                    detail="GitHub Token 权限不足。请确保 Token 有 repo 权限。"
                )
            elif e.status == 404:
                raise HTTPException(
                    status_code=404,
                    detail="无法访问用户仓库。请检查 Token 权限。"
                )
            raise HTTPException(
                status_code=500,
                detail=f"获取仓库列表时出错: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            )

        repo_list = []
        for repo in repos:
            repo_list.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            })
            # 限制返回数量，避免过多
            if len(repo_list) >= 100:
                break

        logger.info(f"Found {len(repo_list)} repositories")
        return {
            "repos": repo_list,
            "count": len(repo_list),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error getting user repos: {error_detail}")
        error_msg = str(e)
        # 如果是 GitHub API 相关错误，提取更友好的错误信息
        if "404" in error_msg or "Not Found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail="GitHub API 返回 404。请检查 Token 是否正确，或 Token 是否有访问仓库的权限。"
            )
        raise HTTPException(status_code=500, detail=f"获取仓库列表失败: {error_msg}")


# ----- Chat Session Management -----
@app.get("/api/chat/sessions")
async def get_chat_sessions(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get all chat sessions for the current user"""
    try:
        if not user:
            return {"sessions": []}

        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        ).order_by(desc(ChatSession.updated_at)).all()

        return {
            "sessions": [
                {
                    "id": s.id,
                    "title": s.title,
                    "repo": s.repo,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get a specific chat session with messages"""
    try:
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="对话不存在")

        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

        return {
            "id": session.id,
            "title": session.title,
            "repo": session.repo,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                }
                for m in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/sessions")
async def create_chat_session(
    request: CreateSessionRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a new chat session"""
    try:
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        session = ChatSession(
            user_id=user.id,
            title=request.title or "New chat",
            repo=request.repo
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return {
            "id": session.id,
            "title": session.title,
            "repo": session.repo,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class SaveHistoryRequest(BaseModel):
    session_id: int
    messages: List[Dict[str, str]]


@app.post("/api/chat/sessions/{session_id}/messages")
async def save_chat_messages(
    session_id: int,
    request: SaveHistoryRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Save chat messages to a session"""
    try:
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 检查是否已存在消息，避免重复保存
        existing_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count()

        # 只保存新消息（如果已有消息，跳过）
        if existing_count == 0 and request.messages:
            # 保存消息到数据库
            for msg in request.messages:
                chat_msg = ChatMessage(
                    session_id=session.id,
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                )
                db.add(chat_msg)

            session.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Saved {len(request.messages)} messages to session {session_id}")

        return {"success": True, "count": len(request.messages)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving chat messages: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/chat/sessions/{session_id}")
async def update_chat_session(
    session_id: int,
    request: UpdateSessionRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Update a chat session"""
    try:
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="对话不存在")

        if request.title is not None:
            session.title = request.title
        if request.repo is not None:
            session.repo = request.repo

        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)

        return {
            "id": session.id,
            "title": session.title,
            "repo": session.repo,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat session: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Delete a chat session"""
    try:
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="对话不存在")

        db.delete(session)
        db.commit()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
