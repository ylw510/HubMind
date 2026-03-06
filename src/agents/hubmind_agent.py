"""
HubMind Main Agent - LangChain Integration
"""
from typing import List, Dict, Optional, Any
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.tools.github_trending import GitHubTrendingTool
from src.tools.github_pr import GitHubPRTool
from src.tools.github_issue import GitHubIssueTool
from src.tools.langchain_tools import create_github_tools
from src.utils.llm_factory import LLMFactory
from src.utils.logger import get_logger
from src.utils.langchain_checkpointer import create_checkpointer
from config import Config

# Setup logger
logger = get_logger(__name__)


class HubMindAgent:
    """Main HubMind Agent powered by LangChain"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        github_token: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        checkpointer=None,
    ):
        """
        Initialize HubMind Agent

        Args:
            provider: LLM provider (openai, anthropic, google, azure, ollama, groq, deepseek, openai_compatible)
            model_name: Model name (optional)
            temperature: Model temperature
            github_token: Optional override for GitHub token
            llm_api_key: Optional override for LLM API key
            llm_base_url: For openai_compatible provider
            llm_model: For openai_compatible provider (model name)
        """
        use_overrides = bool(github_token and llm_api_key)
        if not use_overrides:
            Config.validate()

        provider = (provider or Config.LLM_PROVIDER).lower()
        model_name = model_name or Config.LLM_MODEL or llm_model or None

        llm_kwargs = {}
        if llm_api_key:
            llm_kwargs["api_key"] = llm_api_key
        if provider == "openai_compatible" and llm_base_url:
            llm_kwargs["base_url"] = llm_base_url.rstrip("/")
        if provider == "openai_compatible" and (llm_model or model_name):
            llm_kwargs["model"] = llm_model or model_name
            model_name = llm_model or model_name

        self.llm = LLMFactory.create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            **llm_kwargs
        )

        # Initialize tools (with optional user github token；trending 总结使用同套 LLM)
        self.trending_tool = GitHubTrendingTool(
            github_token=github_token,
            llm_provider=provider,
            llm_api_key=llm_api_key,
        )
        self.pr_tool = GitHubPRTool(github_token=github_token)
        self.issue_tool = GitHubIssueTool(github_token=github_token)

        # Create LangChain tools using modern @tool decorator
        self.tools = create_github_tools(
            trending_tool=self.trending_tool,
            pr_tool=self.pr_tool,
            issue_tool=self.issue_tool
        )

        # Store checkpointer if provided
        self.checkpointer = checkpointer

        # Create agent using LangChain 1.2+ API
        self.agent = self._create_agent()

    # Note: Tools are now created using create_github_tools() from langchain_tools module
    # This uses LangChain's modern @tool decorator with structured inputs (Pydantic models)
    # Old wrapper methods have been removed and replaced with structured tool definitions

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

**IMPORTANT: Output Format Requirements**

You MUST format your responses using proper Markdown syntax:

1. **Use Headings**: Always use proper heading hierarchy
   - Use `# Title` for main titles (level 1)
   - Use `## Section` for major sections (level 2)
   - Use `### Subsection` for subsections (level 3)
   - Use `#### Details` for details (level 4)

2. **Use Links**: Always format URLs as clickable Markdown links
   - Format: `[Link Text](https://url.com)`
   - Example: `[View Repository](https://github.com/owner/repo)`
   - NEVER output raw URLs without Markdown link format

3. **Use Lists**: Use bullet points or numbered lists for multiple items
   - Use `- Item` for unordered lists
   - Use `1. Item` for ordered lists

4. **Use Code Blocks**: For code snippets, use triple backticks with language
   - Format: ` ```language\ncode\n``` `

5. **Use Bold/Italic**: Use `**bold**` and `*italic*` for emphasis

6. **Structure**: Organize your response with clear sections using headings

Example format:
```markdown
# Main Title

## Section 1

Content here with [links](https://example.com).

### Subsection

More details...

## Section 2

- Item 1
- Item 2
```

Always be helpful, concise, and provide actionable insights. Format your responses properly with clear sections, headings, and clickable links."""

        # Use LangChain 1.2+ create_agent API (unified for all LLMs)
        # Note: create_agent returns a CompiledStateGraph, not a simple callable
        agent_kwargs = {
            "model": self.llm,
            "tools": self.tools,
            "system_prompt": system_prompt,
            "debug": False  # Disable debug to reduce output
        }

        # Add checkpointer if available
        if self.checkpointer:
            checkpointer_instance = self.checkpointer.get_checkpointer()
            if checkpointer_instance:
                agent_kwargs["checkpointer"] = checkpointer_instance

        agent_graph = create_agent(**agent_kwargs)
        return agent_graph

    def _supports_tool_calling(self) -> bool:
        """Check if the LLM supports tool calling"""
        # Most modern LLMs support tool calling
        # OpenAI, Anthropic, Google Gemini, DeepSeek, etc. all support it
        provider = Config.LLM_PROVIDER.lower()
        tool_calling_providers = ["deepseek", "openai", "anthropic", "google", "azure", "groq", "openai_compatible"]
        return provider in tool_calling_providers

    # Note: Tool wrapper methods have been moved to langchain_tools.py
    # They are now defined using @tool decorator with structured inputs (Pydantic models)
    # This provides better type safety, validation, and LLM understanding

    def chat(self, message: str, chat_history: Optional[List] = None, session_id: Optional[int] = None) -> str:
        """
        Chat with the agent

        Args:
            message: User message
            chat_history: Previous conversation history (deprecated, use session_id instead)
            session_id: Session ID to use as thread_id for LangChain memory

        Returns:
            Agent response
        """
        try:
            # Use session_id as thread_id if provided, otherwise fallback to hash
            if session_id:
                thread_id = str(session_id)
            else:
                import hashlib
                thread_id = hashlib.md5(message.encode()).hexdigest()[:8]

            config = {"configurable": {"thread_id": thread_id}}

            # Prepare input - LangChain 1.2+ expects messages in the input
            # 如果有历史消息，包含在输入中
            messages_list = []

            # 添加历史消息（如果提供）
            if chat_history:
                # chat_history 可能是 List[Dict] 或 List[Message]
                for msg in chat_history:
                    if isinstance(msg, dict):
                        # 字典格式：{"role": "user", "content": "..."}
                        if msg.get("role") == "user":
                            messages_list.append(HumanMessage(content=msg.get("content", "")))
                        elif msg.get("role") == "assistant":
                            messages_list.append(AIMessage(content=msg.get("content", "")))
                    elif isinstance(msg, (HumanMessage, AIMessage)):
                        # 已经是 LangChain Message 对象
                        messages_list.append(msg)

            # 添加当前用户消息
            messages_list.append(HumanMessage(content=message))

            input_data = {"messages": messages_list}

            # Invoke agent - handle potential connection issues
            try:
                result = self.agent.invoke(input_data, config)
            except (BrokenPipeError, ConnectionError, OSError) as conn_error:
                # Retry once with a new thread_id if connection error
                import time
                time.sleep(0.5)  # Brief delay before retry
                thread_id = hashlib.md5(f"{message}_{time.time()}".encode()).hexdigest()[:8]
                config = {"configurable": {"thread_id": thread_id}}
                result = self.agent.invoke(input_data, config)

            # Extract response from agent output
            # LangChain 1.2+ returns a dict with 'messages' key
            if isinstance(result, dict):
                if "messages" in result and len(result["messages"]) > 0:
                    # Get the last AI message
                    messages = result["messages"]
                    # Find the last AIMessage
                    for msg in reversed(messages):
                        if hasattr(msg, "content"):
                            content = msg.content
                            if content and content.strip():
                                return content
                        elif isinstance(msg, dict):
                            if "content" in msg and msg["content"]:
                                return msg["content"]
                    # Fallback: return last message as string
                    return str(messages[-1])
                elif "output" in result:
                    return result["output"]
                else:
                    # Try to extract any text from the result
                    return str(result)
            elif hasattr(result, "content"):
                return result.content
            else:
                return str(result)
        except (BrokenPipeError, ConnectionError, OSError) as conn_error:
            return "连接中断，请刷新页面重试。"
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            # Log error for debugging (but don't expose to user)
            logger.error(f"Agent error: {str(e)}")
            logger.debug(f"Error detail: {error_detail}")
            return f"处理请求时出错: {str(e)}。请检查配置是否正确。"

    def chat_stream(self, message: str, chat_history: Optional[List] = None, session_id: Optional[int] = None):
        """
        Chat with the agent using streaming (synchronous generator)

        Args:
            message: User message
            chat_history: Previous conversation history (deprecated, use session_id instead)
            session_id: Session ID to use as thread_id for LangChain memory

        Yields:
            Chunks of agent response text
        """
        try:
            # Use session_id as thread_id if provided, otherwise fallback to hash
            if session_id:
                thread_id = str(session_id)
            else:
                import hashlib
                thread_id = hashlib.md5(message.encode()).hexdigest()[:8]

            config = {"configurable": {"thread_id": thread_id}}

            # Prepare input - LangChain 1.2+ expects messages in the input
            # 如果有历史消息，包含在输入中
            messages_list = []

            # 添加历史消息（如果提供）
            if chat_history:
                # chat_history 可能是 List[Dict] 或 List[Message]
                for msg in chat_history:
                    if isinstance(msg, dict):
                        # 字典格式：{"role": "user", "content": "..."}
                        if msg.get("role") == "user":
                            messages_list.append(HumanMessage(content=msg.get("content", "")))
                        elif msg.get("role") == "assistant":
                            messages_list.append(AIMessage(content=msg.get("content", "")))
                    elif isinstance(msg, (HumanMessage, AIMessage)):
                        # 已经是 LangChain Message 对象
                        messages_list.append(msg)

            # 添加当前用户消息
            messages_list.append(HumanMessage(content=message))

            input_data = {"messages": messages_list}

            # Stream agent response
            try:
                # Track previous content to only yield deltas
                # Use a list to accumulate all AI message contents (to handle tool calls)
                accumulated_ai_content = []  # List of all AI message contents seen so far
                previous_content = ""
                chunk_count = 0
                has_yielded = False

                # Use stream() method for state-level streaming (more reliable)
                stream_gen = self.agent.stream(input_data, config)

                for chunk in stream_gen:
                    chunk_count += 1
                    current_content = ""

                    # LangChain agent.stream() yields state dictionaries
                    if isinstance(chunk, dict):
                        # Check for messages in the state (multiple possible structures)
                        messages = None
                        current_content = ""  # Initialize here

                        # Structure 1: chunk["messages"] (direct)
                        if "messages" in chunk:
                            messages = chunk["messages"]

                        # Structure 2: chunk["model"]["messages"] (nested)
                        if "model" in chunk:
                            model_data = chunk["model"]
                            if isinstance(model_data, dict):
                                if "messages" in model_data:
                                    messages = model_data["messages"]
                                # Also check for direct content in model
                                elif "content" in model_data:
                                    content = model_data["content"]
                                    if isinstance(content, list):
                                        # Content might be a list of content blocks
                                        for block in content:
                                            if isinstance(block, dict) and "text" in block:
                                                current_content = block["text"]
                                                break
                                            elif isinstance(block, str):
                                                current_content = block
                                                break
                                    elif isinstance(content, str):
                                        current_content = content

                        # Structure 3: chunk["agent"]["messages"] (nested)
                        if "agent" in chunk and isinstance(chunk["agent"], dict) and not messages:
                            if "messages" in chunk["agent"]:
                                messages = chunk["agent"]["messages"]

                        # Extract content from messages if found
                        if messages:
                            # Collect ALL AI messages in this chunk (to handle tool calls properly)
                            chunk_ai_contents = []
                            for idx, msg in enumerate(messages):
                                # Skip tool calls and human messages, only process AI messages
                                msg_type = None
                                if hasattr(msg, "type"):
                                    msg_type = msg.type
                                elif isinstance(msg, dict) and "type" in msg:
                                    msg_type = msg["type"]

                                # Also check class name for AIMessage
                                if not msg_type and hasattr(msg, "__class__"):
                                    class_name = msg.__class__.__name__
                                    if "AI" in class_name or "Assistant" in class_name:
                                        msg_type = "ai"

                                # Skip non-AI messages (but allow if type is None/unknown - might be AI message)
                                if msg_type and msg_type not in ["ai", "AIMessage", "AssistantMessage"]:
                                    continue

                                # Try to extract content
                                content_found = False
                                msg_content = None
                                if hasattr(msg, "content"):
                                    content = msg.content
                                    if content:
                                        # If content is a list (e.g., from LangChain message format)
                                        if isinstance(content, list):
                                            for block in content:
                                                if isinstance(block, dict) and "text" in block:
                                                    msg_content = block["text"]
                                                    content_found = True
                                                    break
                                                elif isinstance(block, str):
                                                    msg_content = block
                                                    content_found = True
                                                    break
                                        else:
                                            msg_content = str(content)
                                            content_found = True

                                        if content_found and msg_content and str(msg_content).strip():
                                            chunk_ai_contents.append(str(msg_content).strip())

                                if not content_found and isinstance(msg, dict):
                                    if "content" in msg:
                                        content = msg["content"]
                                        if isinstance(content, list):
                                            for block in content:
                                                if isinstance(block, dict) and "text" in block:
                                                    msg_content = block["text"]
                                                    content_found = True
                                                    break
                                                elif isinstance(block, str):
                                                    msg_content = block
                                                    content_found = True
                                                    break
                                        else:
                                            msg_content = str(content)
                                            content_found = True

                                        if content_found and msg_content and str(msg_content).strip():
                                            chunk_ai_contents.append(str(msg_content).strip())

                            # Combine all AI messages from this chunk
                            if chunk_ai_contents:
                                # Join with newlines to separate different AI responses
                                current_content = "\n".join(chunk_ai_contents)
                            else:
                                current_content = ""

                        # Also check for "output" key
                        elif "output" in chunk:
                            output = chunk["output"]
                            if isinstance(output, str):
                                current_content = output
                            elif hasattr(output, "content"):
                                current_content = output.content
                    elif hasattr(chunk, "content"):
                        if chunk.content:
                            current_content = chunk.content
                    elif isinstance(chunk, str):
                        current_content = chunk
                    else:
                        logger.warning(f"Unknown chunk type: {type(chunk)}")

                    # Convert to string for comparison
                    current_content_str = str(current_content) if current_content else ""

                    # Accumulate AI content: add new content that we haven't seen before
                    # This handles the case where tool calls reset the message list
                    if current_content_str:
                        # Check if this content is already in our accumulated list
                        is_new_content = True
                        for existing_content in accumulated_ai_content:
                            if current_content_str in existing_content or existing_content in current_content_str:
                                # If current is a substring of existing, it's not new
                                if len(current_content_str) <= len(existing_content):
                                    is_new_content = False
                                    break
                                # If current contains existing, replace it
                                else:
                                    accumulated_ai_content.remove(existing_content)
                                    break

                        if is_new_content:
                            accumulated_ai_content.append(current_content_str)

                    # Build full accumulated content
                    full_accumulated_content = "\n".join(accumulated_ai_content)
                    previous_content_str = str(previous_content) if previous_content else ""

                    # Yield only new content (delta) - compare accumulated content with previous
                    if full_accumulated_content and len(full_accumulated_content) > len(previous_content_str):
                        delta = full_accumulated_content[len(previous_content_str):]
                        if delta:
                            # Split delta into smaller chunks for better streaming experience
                            chunk_size = 15  # Characters per yield for smoother streaming
                            for i in range(0, len(delta), chunk_size):
                                piece = delta[i:i + chunk_size]
                                if piece:
                                    yield piece
                                    has_yielded = True
                                    # Small delay to make streaming more visible
                                    import time
                                    time.sleep(0.01)  # 10ms delay for smoother display
                        previous_content = full_accumulated_content

                # If no content was yielded, log a warning with more details
                if not has_yielded:
                    if chunk_count > 0:
                        logger.warning(f"[AGENT_STREAM] No content yielded after {chunk_count} chunks. Last chunk type: {type(chunk)}, value: {str(chunk)[:300]}")
                    else:
                        logger.warning(f"[AGENT_STREAM] No chunks received from agent.stream()")
                else:
                    logger.debug(f"[AGENT_STREAM] Streaming completed: {chunk_count} chunks, {len(previous_content)} chars yielded")

            except (BrokenPipeError, ConnectionError, OSError) as conn_error:
                logger.warning(f"Connection error during streaming: {str(conn_error)}")
                yield f"\n\n连接错误: {str(conn_error)}。请重试。"
            except Exception as e:
                logger.error(f"Error in chat_stream: {str(e)}")
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
                yield f"\n\n处理消息时出错: {str(e)}"
        except Exception as e:
            logger.error(f"Error in chat_stream: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            yield f"处理消息时出错: {str(e)}"
