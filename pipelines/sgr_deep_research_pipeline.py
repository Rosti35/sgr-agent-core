"""
SGR Deep Research Pipeline for Open WebUI

This pipeline connects Open WebUI to the SGR Deep Research Agent API,
enabling streaming research capabilities with multiple agent types.

Features:
- Connects to SGR Deep Research API with OpenAI-compatible endpoints
- Streaming support for real-time agent responses
- Dynamic model listing from available agents
- Clarification handling for interactive research sessions
"""

import json
import logging
from typing import AsyncGenerator, Callable, List, Optional, Union

import aiohttp
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipeline:
    """SGR Deep Research Pipeline for Open WebUI."""

    class Valves(BaseModel):
        """Configuration options for the pipeline."""

        SGR_API_BASE_URL: str = Field(
            default="http://localhost:8010",
            description="Base URL of the SGR Deep Research API server",
        )
        DEFAULT_MODEL: str = Field(
            default="sgr_tool_calling_agent",
            description="Default agent model to use if none specified",
        )
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="Request timeout in seconds (agent research can take time)",
        )
        EMIT_TOOL_CALLS: bool = Field(
            default=True,
            description="Whether to emit tool calls in the response stream",
        )

    def __init__(self):
        self.name = "SGR Deep Research"
        self.valves = self.Valves()
        self._session: Optional[aiohttp.ClientSession] = None
        self._available_models: List[dict] = []

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.valves.REQUEST_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def on_startup(self):
        """Called when the server is started."""
        logger.info(f"Starting {self.name} pipeline")
        logger.info(f"SGR API URL: {self.valves.SGR_API_BASE_URL}")
        await self._fetch_available_models()

    async def on_shutdown(self):
        """Called when the server is stopped."""
        logger.info(f"Shutting down {self.name} pipeline")
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch_available_models(self) -> List[dict]:
        """Fetch available models from the SGR API."""
        try:
            session = await self._get_session()
            url = f"{self.valves.SGR_API_BASE_URL}/v1/models"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self._available_models = data.get("data", [])
                    logger.info(f"Loaded {len(self._available_models)} agent models")
                    return self._available_models
                else:
                    logger.warning(f"Failed to fetch models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    async def on_valves_updated(self):
        """Called when valves are updated."""
        logger.info("Valves updated, refreshing models...")
        await self._fetch_available_models()

    def pipelines(self) -> List[dict]:
        """Return list of available pipelines/models."""
        if not self._available_models:
            # Return default if models haven't been fetched yet
            return [
                {
                    "id": "sgr_tool_calling_agent",
                    "name": "SGR Tool Calling Agent",
                },
                {
                    "id": "sgr_research_agent",
                    "name": "SGR Research Agent",
                },
            ]

        return [
            {
                "id": model.get("id", "unknown"),
                "name": model.get("id", "Unknown Agent").replace("_", " ").title(),
            }
            for model in self._available_models
        ]

    async def inlet(
        self, body: dict, user: Optional[dict] = None
    ) -> dict:
        """Pre-process incoming requests."""
        logger.debug(f"Inlet received body: {body}")
        return body

    async def outlet(
        self, body: dict, user: Optional[dict] = None
    ) -> dict:
        """Post-process outgoing responses."""
        return body

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable] = None,
        __task__: Optional[str] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Main pipeline method that processes requests and streams responses.

        Args:
            body: Request body containing messages and model info
            __user__: User information from Open WebUI
            __event_emitter__: Event emitter for status updates
            __task__: Task type (e.g., "title_generation")

        Returns:
            Either a string response or an async generator for streaming
        """
        # Handle title generation requests
        if __task__ == "title_generation":
            return "Research Session"

        # Extract model and messages from body
        model_id = body.get("model", self.valves.DEFAULT_MODEL)
        messages = body.get("messages", [])

        # Handle pipeline model ID format (e.g., "sgr_deep_research.sgr_tool_calling_agent")
        if "." in model_id:
            model_id = model_id.split(".")[-1]

        logger.info(f"Processing request with model: {model_id}")

        # Get the user message
        user_message = self._extract_user_message(messages)
        if not user_message:
            return "No user message found in the request."

        # Check if task is specified in body (Open WebUI sometimes uses this)
        if body.get("title", False):
            return "SGR Research"

        # Stream the response
        return self._stream_response(model_id, messages, __event_emitter__)

    def _extract_user_message(self, messages: List[dict]) -> Optional[str]:
        """Extract the latest user message from the conversation."""
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Handle multi-modal messages
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text", "")
                        elif isinstance(item, str):
                            return item
        return None

    async def _stream_response(
        self,
        model_id: str,
        messages: List[dict],
        event_emitter: Optional[Callable] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from the SGR API.

        Args:
            model_id: The agent model to use
            messages: Conversation messages
            event_emitter: Optional event emitter for status updates

        Yields:
            String chunks of the response
        """
        session = await self._get_session()
        url = f"{self.valves.SGR_API_BASE_URL}/v1/chat/completions"

        # Prepare the request payload
        payload = {
            "model": model_id,
            "messages": [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in messages
            ],
            "stream": True,
        }

        # Emit status if event emitter is available
        if event_emitter:
            await self._emit_status(event_emitter, "info", f"Starting research with {model_id}...")

        try:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    if event_emitter:
                        await self._emit_status(event_emitter, "error", f"API Error: {error_text}")
                    yield f"Error: {error_text}"
                    return

                # Get agent ID from response headers for tracking
                agent_id = response.headers.get("X-Agent-ID", "")
                if agent_id:
                    logger.info(f"Agent ID: {agent_id}")

                # Process SSE stream
                buffer = ""
                async for chunk in response.content.iter_any():
                    if not chunk:
                        continue

                    buffer += chunk.decode("utf-8")

                    # Process complete SSE events
                    while "\n\n" in buffer:
                        event, buffer = buffer.split("\n\n", 1)

                        for line in event.split("\n"):
                            if line.startswith("data: "):
                                data = line[6:]  # Remove "data: " prefix

                                if data == "[DONE]":
                                    logger.info("Stream completed")
                                    if event_emitter:
                                        await self._emit_status(event_emitter, "info", "Research completed")
                                    return

                                try:
                                    parsed = json.loads(data)
                                    content = self._extract_content_from_chunk(parsed)
                                    if content:
                                        yield content

                                    # Handle tool calls (emit as status)
                                    tool_call = self._extract_tool_call_from_chunk(parsed)
                                    if tool_call and self.valves.EMIT_TOOL_CALLS:
                                        if event_emitter:
                                            await self._emit_status(
                                                event_emitter,
                                                "info",
                                                f"🔧 {tool_call['name']}",
                                                done=False,
                                            )
                                        # Optionally yield tool call info as formatted text
                                        yield f"\n\n> **Tool:** {tool_call['name']}\n"
                                        if tool_call.get("arguments"):
                                            try:
                                                args = json.loads(tool_call["arguments"])
                                                # Format arguments nicely
                                                formatted_args = self._format_tool_arguments(args)
                                                if formatted_args:
                                                    yield f"> {formatted_args}\n\n"
                                            except json.JSONDecodeError:
                                                pass

                                    # Check for finish reason
                                    finish_reason = self._get_finish_reason(parsed)
                                    if finish_reason:
                                        logger.info(f"Finish reason: {finish_reason}")

                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse JSON: {e}")
                                    continue

        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            if event_emitter:
                await self._emit_status(event_emitter, "error", f"Connection error: {str(e)}")
            yield f"Connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            if event_emitter:
                await self._emit_status(event_emitter, "error", f"Error: {str(e)}")
            yield f"Error: {str(e)}"

    def _extract_content_from_chunk(self, chunk: dict) -> Optional[str]:
        """Extract text content from an OpenAI-format streaming chunk."""
        try:
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content")
        except (KeyError, IndexError):
            pass
        return None

    def _extract_tool_call_from_chunk(self, chunk: dict) -> Optional[dict]:
        """Extract tool call information from a streaming chunk."""
        try:
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                tool_calls = delta.get("tool_calls")
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    function = tool_call.get("function", {})
                    return {
                        "id": tool_call.get("id", ""),
                        "name": function.get("name", ""),
                        "arguments": function.get("arguments", ""),
                    }
        except (KeyError, IndexError):
            pass
        return None

    def _get_finish_reason(self, chunk: dict) -> Optional[str]:
        """Get finish reason from a streaming chunk."""
        try:
            choices = chunk.get("choices", [])
            if choices:
                return choices[0].get("finish_reason")
        except (KeyError, IndexError):
            pass
        return None

    def _format_tool_arguments(self, args: dict) -> str:
        """Format tool arguments for display."""
        formatted_parts = []
        for key, value in args.items():
            if key in ("reasoning", "thought", "plan", "analysis"):
                continue  # Skip verbose reasoning fields
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            formatted_parts.append(f"**{key}**: {value}")
        return " | ".join(formatted_parts[:3])  # Limit to 3 args

    async def _emit_status(
        self,
        emitter: Callable,
        level: str,
        message: str,
        done: bool = False,
    ):
        """Emit a status event to Open WebUI."""
        try:
            await emitter(
                {
                    "type": "status",
                    "data": {
                        "status": level,
                        "description": message,
                        "done": done,
                    },
                }
            )
        except Exception as e:
            logger.warning(f"Failed to emit status: {e}")


# Alternative synchronous version for compatibility
class SyncPipeline:
    """Synchronous wrapper for environments that don't support async generators."""

    def __init__(self):
        self._pipeline = Pipeline()
        self.name = self._pipeline.name
        self.valves = self._pipeline.valves

    async def on_startup(self):
        await self._pipeline.on_startup()

    async def on_shutdown(self):
        await self._pipeline.on_shutdown()

    def pipelines(self) -> List[dict]:
        return self._pipeline.pipelines()

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Synchronous pipe method for compatibility."""
        import asyncio

        # Handle title generation
        if body.get("title", False):
            return "SGR Research"

        # Create async wrapper
        async def async_pipe():
            result = []
            async for chunk in self._pipeline._stream_response(model_id, messages):
                result.append(chunk)
            return "".join(result)

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, return the generator
                return self._pipeline._stream_response(model_id, messages)
            else:
                return loop.run_until_complete(async_pipe())
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(async_pipe())

