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
        agent_graph = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            debug=False  # Disable debug to reduce output
        )
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
            # Use a consistent thread_id for the session
            import hashlib
            thread_id = hashlib.md5(message.encode()).hexdigest()[:8]
            config = {"configurable": {"thread_id": thread_id}}

            # Prepare input - LangChain 1.2+ expects messages in the input
            input_data = {"messages": [HumanMessage(content=message)]}

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

    def chat_stream(self, message: str, chat_history: Optional[List] = None):
        """
        Chat with the agent using streaming (synchronous generator)

        Args:
            message: User message
            chat_history: Previous conversation history

        Yields:
            Chunks of agent response text
        """
        try:
            import hashlib
            thread_id = hashlib.md5(message.encode()).hexdigest()[:8]
            config = {"configurable": {"thread_id": thread_id}}

            # Prepare input - LangChain 1.2+ expects messages in the input
            input_data = {"messages": [HumanMessage(content=message)]}

            # Stream agent response
            try:
                # Track previous content to only yield deltas
                previous_content = ""
                chunk_count = 0
                has_yielded = False

                # Use stream_events for more granular streaming (token-level)
                # This provides better real-time streaming experience
                logger.debug(f"[AGENT_STREAM] Starting to stream agent response...")
                logger.debug(f"[AGENT_STREAM] Input data: {input_data}")
                logger.debug(f"[AGENT_STREAM] Config: {config}")
                logger.debug(f"[AGENT_STREAM] Agent type: {type(self.agent)}")

                # Try to use stream_events for token-level streaming
                try:
                    # Check if agent has stream_events method
                    if hasattr(self.agent, 'stream_events'):
                        logger.debug("[AGENT_STREAM] Using stream_events for token-level streaming")
                        stream_gen = self.agent.stream_events(input_data, config, version="v2")
                    else:
                        logger.debug("[AGENT_STREAM] Using stream() method (state-level streaming)")
                        stream_gen = self.agent.stream(input_data, config)
                except Exception as e:
                    logger.warning(f"[AGENT_STREAM] stream_events not available, falling back to stream(): {str(e)}")
                    stream_gen = self.agent.stream(input_data, config)

                logger.debug(f"[AGENT_STREAM] Stream generator created: {type(stream_gen)}")

                for chunk in stream_gen:
                    chunk_count += 1
                    logger.debug(f"[AGENT_STREAM] Received chunk #{chunk_count}, type: {type(chunk)}")

                    # Extract text from chunk
                    current_content = ""

                    # Log first few chunks for debugging (only in DEBUG mode)
                    if chunk_count <= 3:
                        logger.debug(f"[AGENT_STREAM] Chunk #{chunk_count} type: {type(chunk)}, value: {str(chunk)[:200]}")

                    # LangChain agent.stream() yields state dictionaries
                    if isinstance(chunk, dict):
                        logger.debug(f"[AGENT_STREAM] Chunk #{chunk_count} is dict, keys: {list(chunk.keys())}")

                        # Check for messages in the state (multiple possible structures)
                        messages = None

                        # Structure 1: chunk["messages"] (direct)
                        if "messages" in chunk:
                            messages = chunk["messages"]
                            logger.debug(f"[AGENT_STREAM] Found messages directly: {len(messages)} messages")

                        # Structure 2: chunk["model"]["messages"] (nested)
                        elif "model" in chunk and isinstance(chunk["model"], dict):
                            if "messages" in chunk["model"]:
                                messages = chunk["model"]["messages"]
                                logger.debug(f"[AGENT_STREAM] Found messages in model: {len(messages)} messages")

                        # Structure 3: chunk["agent"]["messages"] (nested)
                        elif "agent" in chunk and isinstance(chunk["agent"], dict):
                            if "messages" in chunk["agent"]:
                                messages = chunk["agent"]["messages"]
                                logger.debug(f"[AGENT_STREAM] Found messages in agent: {len(messages)} messages")

                        # Extract content from messages if found
                        if messages:
                            logger.debug(f"[AGENT_STREAM] Processing {len(messages)} messages")
                            # Get the last message in the chunk
                            for idx, msg in enumerate(reversed(messages)):
                                logger.debug(f"[AGENT_STREAM] Checking message {idx}, type: {type(msg)}")
                                if hasattr(msg, "content"):
                                    content = msg.content
                                    logger.debug(f"[AGENT_STREAM] Message has content attribute: {type(content)}, length: {len(str(content)) if content else 0}")
                                    if content:
                                        current_content = content
                                        logger.debug(f"[AGENT_STREAM] Found content in message: {str(content)[:100]}...")
                                        break
                                elif isinstance(msg, dict):
                                    logger.debug(f"[AGENT_STREAM] Message is dict, keys: {list(msg.keys())}")
                                    if "content" in msg:
                                        current_content = msg["content"]
                                        logger.debug(f"[AGENT_STREAM] Found content in dict message: {str(current_content)[:100]}...")
                                        break

                        # Also check for "output" key
                        elif "output" in chunk:
                            logger.debug(f"[AGENT_STREAM] Found 'output' key in chunk")
                            output = chunk["output"]
                            if isinstance(output, str):
                                current_content = output
                                logger.debug(f"[AGENT_STREAM] Output is string: {current_content[:100]}...")
                            elif hasattr(output, "content"):
                                current_content = output.content
                                logger.debug(f"[AGENT_STREAM] Output has content: {str(current_content)[:100]}...")

                        # Log chunk structure for debugging (only first few chunks)
                        if chunk_count <= 3:
                            logger.debug(f"[AGENT_STREAM] Chunk #{chunk_count} keys: {list(chunk.keys())}")
                            if "model" in chunk:
                                logger.debug(f"[AGENT_STREAM] Chunk #{chunk_count} model keys: {list(chunk['model'].keys()) if isinstance(chunk['model'], dict) else 'not dict'}")
                    elif hasattr(chunk, "content"):
                        logger.debug(f"[AGENT_STREAM] Chunk has content attribute")
                        if chunk.content:
                            current_content = chunk.content
                            logger.debug(f"[AGENT_STREAM] Content from attribute: {str(current_content)[:100]}...")
                    elif isinstance(chunk, str):
                        logger.debug(f"[AGENT_STREAM] Chunk is string")
                        current_content = chunk
                        logger.debug(f"[AGENT_STREAM] Content is string: {current_content[:100]}...")
                    else:
                        logger.warning(f"[AGENT_STREAM] Unknown chunk type: {type(chunk)}")

                    logger.debug(f"[AGENT_STREAM] Extracted content length: {len(current_content)}, previous: {len(previous_content)}")

                    # Yield only new content (delta) - for state-based streaming
                    if current_content and len(current_content) > len(previous_content):
                        delta = current_content[len(previous_content):]
                        if delta:
                            # Split delta into smaller chunks for better streaming experience
                            # Yield in smaller pieces (e.g., 10-20 chars at a time) for smoother display
                            chunk_size = 15  # Characters per yield for smoother streaming
                            for i in range(0, len(delta), chunk_size):
                                piece = delta[i:i + chunk_size]
                                if piece:
                                    logger.debug(f"[AGENT_STREAM] Yielding piece: {len(piece)} chars")
                                    yield piece
                                    has_yielded = True
                                    # Small delay to make streaming more visible (optional)
                                    import time
                                    time.sleep(0.01)  # 10ms delay for smoother display
                        previous_content = current_content
                    elif not current_content:
                        logger.debug(f"[AGENT_STREAM] No new content to yield (current: {len(current_content)}, previous: {len(previous_content)})")

                    # Log progress for debugging (every 50 chunks, only in DEBUG mode)
                    if chunk_count % 50 == 0:
                        logger.debug(f"[AGENT_STREAM] Progress: {chunk_count} chunks processed, content length: {len(previous_content)}")

                logger.debug(f"[AGENT_STREAM] Stream loop finished. Total chunks: {chunk_count}, has_yielded: {has_yielded}")

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
