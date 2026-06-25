"""
GeminiToolAdapter — Agentic Function Calling + Native Code Execution

Extends GeminiAdapter with:
  • Multi-turn function-calling loop  (skills and organs as Gemini tools)
  • Parallel dispatch of concurrent function calls via asyncio.gather()
  • Gemini built-in Code Execution sandbox (server-side Python runner)
  • Full rate-limit retry / key-rotation inherited from GeminiAdapter._api_call()

Usage
─────
    dispatcher = SynapticToolDispatcher(skill_registry)
    adapter = GeminiToolAdapter(dispatcher)
    result = await adapter.generate(system_prompt, task_prompt)
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from google.genai import types

from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter
from synaptic.utils.exceptions import ModelProviderError
from synaptic.utils.logger import synaptic_log

if TYPE_CHECKING:
    from synaptic.core.tool_dispatcher import SynapticToolDispatcher


class GeminiToolAdapter(GeminiAdapter):
    """
    Agentic Gemini adapter with structured function calling.

    The agentic loop
    ────────────────
    1. Send system prompt + user task with tool declarations attached.
    2. If Gemini returns function_call parts → execute them in parallel.
    3. Append the model turn and all function responses to the conversation.
    4. Repeat until Gemini returns a plain-text response (done) or
       MAX_TOOL_ROUNDS is reached.

    Falls back to plain GeminiAdapter.generate() when:
      • No dispatcher is provided
      • The model returns no function calls on the first turn
    """

    def __init__(self, dispatcher: Optional["SynapticToolDispatcher"] = None) -> None:
        super().__init__()
        self._dispatcher = dispatcher
        self._max_rounds = settings.MAX_TOOL_ROUNDS
        self._mcp_session = None   # set by connect_mcp()
        self._mcp_stdio_ctx = None
        self._mcp_session_ctx = None

    # ── public interface ──────────────────────────────────────────────────────

    async def connect_mcp(self) -> None:
        """
        Launches the SynapticMCPServer subprocess and opens a ClientSession.
        Called lazily on the first generate() when MCP_ENABLED=True.
        Safe to call multiple times — no-op if already connected.
        """
        if self._mcp_session is not None:
            return
        try:
            import shlex
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            parts = shlex.split(settings.MCP_SERVER_COMMAND)
            server_params = StdioServerParameters(command=parts[0], args=parts[1:])

            self._mcp_stdio_ctx = stdio_client(server_params)
            read, write = await self._mcp_stdio_ctx.__aenter__()

            self._mcp_session_ctx = ClientSession(read, write)
            session = await self._mcp_session_ctx.__aenter__()
            await session.initialize()

            self._mcp_session = session
            synaptic_log.info("[GeminiTool] MCP ClientSession connected to SynapticMCPServer")
        except Exception as exc:
            synaptic_log.warning(f"[GeminiTool] MCP connect failed ({exc}) — continuing without MCP tools")
            self._mcp_session = None

    async def aclose(self) -> None:
        """Cleanly shut down the MCP subprocess and session."""
        for ctx in (self._mcp_session_ctx, self._mcp_stdio_ctx):
            if ctx is not None:
                try:
                    await ctx.__aexit__(None, None, None)
                except Exception:
                    pass
        self._mcp_session = None
        self._mcp_stdio_ctx = None
        self._mcp_session_ctx = None

    async def generate(self, system_instruction: str, prompt: str) -> str:
        """
        Overrides base generate() with an agentic function-calling loop.
        Uses the inherited _api_call() for all actual Gemini API calls so
        rate-limit handling and key rotation are never duplicated.
        """
        if not self._dispatcher and not settings.GEMINI_USE_CODE_EXECUTION and not settings.MCP_ENABLED:
            return await super().generate(system_instruction, prompt)

        # Lazy MCP connect — first call starts the server subprocess
        if settings.MCP_ENABLED and self._mcp_session is None:
            await self.connect_mcp()

        config  = self._build_config(system_instruction)
        contents = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        for round_i in range(1, self._max_rounds + 1):
            response = await self._api_call(contents=contents, config=config)
            candidate = response.candidates[0]

            # Gather any function_call parts from this turn
            fn_calls = [
                part.function_call
                for part in candidate.content.parts
                if getattr(part, "function_call", None)
            ]

            # No function calls → model is done; return final text
            if not fn_calls:
                return self._extract_text(candidate)

            synaptic_log.debug(
                f"[GeminiTool] Round {round_i}: {len(fn_calls)} function call(s): "
                + ", ".join(fc.name for fc in fn_calls)
            )

            # Append the model's turn to conversation history
            contents.append(candidate.content)

            # Execute all function calls concurrently
            results = await asyncio.gather(
                *[self._execute_function(fc) for fc in fn_calls]
            )

            # Build function response parts and append user turn
            response_parts = [
                self._build_fn_response(fc, result)
                for fc, result in zip(fn_calls, results)
            ]
            contents.append(
                types.Content(role="user", parts=response_parts)
            )

        raise ModelProviderError(
            f"GeminiToolAdapter: agentic loop exceeded MAX_TOOL_ROUNDS={self._max_rounds}. "
            "Increase MAX_TOOL_ROUNDS in .env or simplify the task."
        )

    # ── private helpers ───────────────────────────────────────────────────────

    def _build_config(self, system_instruction: str) -> types.GenerateContentConfig:
        """Assembles GenerateContentConfig with tools and system instruction."""
        tool_list: list = []

        if self._dispatcher:
            declarations = self._dispatcher.get_function_declarations()
            if declarations:
                tool_list.append(types.Tool(function_declarations=declarations))

        if settings.GEMINI_USE_CODE_EXECUTION:
            tool_list.append(types.Tool(code_execution=types.CodeExecution()))

        # MCP ClientSession — Gemini SDK accepts it directly in the tools list
        if self._mcp_session is not None:
            tool_list.append(self._mcp_session)

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tool_list or None,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            ) if tool_list else None,
        )

    async def _execute_function(self, fn_call) -> str:
        """Dispatches a single function call to the tool dispatcher."""
        if self._dispatcher is None:
            return "[ERROR] No tool dispatcher configured"
        try:
            args = dict(fn_call.args) if fn_call.args else {}
            result = await self._dispatcher.execute(fn_call.name, args)
            synaptic_log.debug(f"[GeminiTool] {fn_call.name}({args}) → {str(result)[:80]}")
            return str(result)
        except Exception as exc:
            synaptic_log.warning(f"[GeminiTool] Tool {fn_call.name} raised: {exc}")
            return f"[ERROR] {exc}"

    @staticmethod
    def _build_fn_response(fn_call, result: str) -> types.Part:
        """Builds a Part.from_function_response, attaching the call ID if present."""
        kwargs: dict = {
            "name":     fn_call.name,
            "response": {"result": result},
        }
        fn_id = getattr(fn_call, "id", None)
        if fn_id:
            kwargs["id"] = fn_id
        return types.Part.from_function_response(**kwargs)

    @staticmethod
    def _extract_text(candidate) -> str:
        """Pulls the text out of a candidate — handles code_execution_result parts too."""
        text_parts = []
        for part in candidate.content.parts:
            if getattr(part, "text", None):
                text_parts.append(part.text)
            # Include code execution output in final answer if present
            cer = getattr(part, "code_execution_result", None)
            if cer and getattr(cer, "output", None):
                text_parts.append(f"\n[CODE OUTPUT]\n{cer.output}")
        return "\n".join(text_parts) if text_parts else ""
