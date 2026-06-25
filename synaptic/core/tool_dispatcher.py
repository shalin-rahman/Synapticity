"""
SynapticToolDispatcher — Tool Registry for Gemini Function Calling

Maps tool names to async callables and generates the JSON schema
(function_declarations) that Gemini needs to invoke them.

Built-in tools (always registered)
────────────────────────────────────
  list_skills          — enumerate loaded skill playbooks
  get_skill_content    — fetch a specific skill's markdown
  read_workspace_file  — read any file inside the workspace

Organ tools (registered when organs are available)
──────────────────────────────────────────────────
  search_memory        — hippocampus semantic lookup
  store_reflection     — hippocampus write
  get_vision_report    — PostHog UX health summary

Adding a new tool
─────────────────
    dispatcher.register(
        name="my_tool",
        fn=my_async_fn,
        description="What this tool does.",
        parameters={"param": {"type": "string", "description": "..."}}
        required=["param"],
    )
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from synaptic.config import settings
from synaptic.utils.logger import synaptic_log


@dataclass
class _ToolRegistration:
    fn:          Callable
    declaration: dict   # full function_declaration dict for Gemini


class SynapticToolDispatcher:
    """
    Central tool registry exposed to GeminiToolAdapter.

    Design: tools are plain Python async callables registered with a JSON
    schema.  Gemini receives the schemas; when it returns a function_call
    the dispatcher looks up the callable and awaits it.
    """

    def __init__(
        self,
        skill_registry=None,
        organs=None,          # SynapticOrganInterface instance, optional
    ) -> None:
        self._registry: Dict[str, _ToolRegistration] = {}
        self._register_builtin_tools()
        if skill_registry is not None:
            self._register_skill_tools(skill_registry)
        if organs is not None:
            self._register_organ_tools(organs)

    # ── public API ────────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        fn: Callable,
        description: str,
        parameters: Dict[str, dict],
        required: Optional[List[str]] = None,
    ) -> None:
        """Register a callable as a Gemini-invocable tool."""
        declaration = {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required or list(parameters.keys()),
            },
        }
        self._registry[name] = _ToolRegistration(fn=fn, declaration=declaration)
        synaptic_log.debug(f"[Dispatcher] Registered tool: {name}")

    def get_function_declarations(self) -> List[dict]:
        """Returns all registered tool schemas for Gemini's GenerateContentConfig."""
        return [reg.declaration for reg in self._registry.values()]

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Dispatches a function call by name. Returns the string result.
        Never raises — errors are returned as '[ERROR] …' strings so the
        agentic loop can continue and self-correct.
        """
        reg = self._registry.get(tool_name)
        if reg is None:
            return (
                f"[ERROR] Unknown tool '{tool_name}'. "
                f"Available: {', '.join(self._registry)}"
            )
        try:
            result = (
                await reg.fn(**args)
                if asyncio.iscoroutinefunction(reg.fn)
                else reg.fn(**args)
            )
            return str(result)
        except Exception as exc:
            synaptic_log.warning(f"[Dispatcher] Tool '{tool_name}' failed: {exc}")
            return f"[ERROR] Tool '{tool_name}' raised: {exc}"

    @property
    def tool_names(self) -> List[str]:
        return list(self._registry.keys())

    # ── built-in tools ────────────────────────────────────────────────────────

    def _register_builtin_tools(self) -> None:

        async def list_skills() -> str:
            """Lists all available technical skill playbooks by folder name."""
            skill_dir = settings.SKILL_PATH
            try:
                names = [
                    d for d in os.listdir(skill_dir)
                    if os.path.isdir(os.path.join(skill_dir, d))
                ]
                return ", ".join(sorted(names)) or "(no skills found)"
            except Exception as exc:
                return f"[ERROR] {exc}"

        async def get_skill_content(skill_name: str) -> str:
            """Returns the markdown content of a named technical skill playbook."""
            candidates = [
                os.path.join(settings.SKILL_PATH, skill_name, "skill.md"),
            ]
            for ext_path in settings.EXTERNAL_SKILL_PATHS:
                candidates.append(os.path.join(ext_path, skill_name, "skill.md"))
            for path in candidates:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as fh:
                        return fh.read()
            return f"[ERROR] Skill '{skill_name}' not found."

        async def read_workspace_file(relative_path: str) -> str:
            """
            Reads a file from the workspace directory.
            relative_path is relative to the workspace root (e.g. 'my-mission/output/app.py').
            """
            full = os.path.join(settings.WORKSPACE_PATH, relative_path)
            if not os.path.exists(full):
                return f"[ERROR] File not found: {relative_path}"
            try:
                with open(full, "r", encoding="utf-8") as fh:
                    return fh.read()
            except Exception as exc:
                return f"[ERROR] Cannot read file: {exc}"

        self.register(
            "list_skills", list_skills,
            "Lists all available technical skill playbooks by name.",
            parameters={},
            required=[],
        )
        self.register(
            "get_skill_content", get_skill_content,
            "Returns the full markdown content of a named skill playbook.",
            parameters={"skill_name": {
                "type": "string",
                "description": "Exact folder name of the skill (e.g. 'api-design')",
            }},
        )
        self.register(
            "read_workspace_file", read_workspace_file,
            "Reads a file from the workspace directory by relative path.",
            parameters={"relative_path": {
                "type": "string",
                "description": "Path relative to workspace root (e.g. 'my-mission/output/app.py')",
            }},
        )

    # ── skill registry tools ──────────────────────────────────────────────────

    def _register_skill_tools(self, skill_registry) -> None:
        """Exposes the live SkillRegistry cache as queryable Gemini tools."""

        async def search_skills(keyword: str) -> str:
            """Searches skill names and content for a keyword. Returns matching skill names."""
            keyword_lower = keyword.lower()
            matches = [
                name for name, data in skill_registry._cache.items()
                if keyword_lower in name.lower()
                or keyword_lower in data.get("content", "").lower()
            ]
            return ", ".join(matches) if matches else "(no matches)"

        self.register(
            "search_skills", search_skills,
            "Searches loaded skills by keyword. Returns matching skill folder names.",
            parameters={"keyword": {
                "type": "string",
                "description": "Keyword to search for in skill names and content",
            }},
        )

    # ── organ tools ───────────────────────────────────────────────────────────

    def _register_organ_tools(self, organs) -> None:
        """Exposes available SynapticOrganInterface methods as Gemini tools."""

        if organs.hippocampus is not None:
            hippocampus = organs.hippocampus

            async def search_memory(query: str, limit: int = 5) -> str:
                """
                Semantic search over past agent reflections and successful fixes
                stored in the Synapticity hippocampus (Supabase + pgvector).
                """
                results = await hippocampus.semantic_lookup(query, limit=limit)
                if not results:
                    return "(no relevant memories found)"
                lines = []
                for r in results:
                    sim = r.get("similarity", 0)
                    lines.append(
                        f"[{r.get('reflection_type','?')} | sim={sim:.2f}]\n"
                        f"{r.get('content','')[:400]}"
                    )
                return "\n\n---\n\n".join(lines)

            async def store_reflection(
                mission_id: str,
                reflection_type: str,
                content: str,
            ) -> str:
                """Stores a new agent reflection into long-term hippocampus memory."""
                row_id = await hippocampus.store_reflection(
                    mission_id=mission_id,
                    agent_name="gemini_tool_agent",
                    reflection_type=reflection_type,
                    content=content,
                )
                return f"Stored reflection {row_id}"

            self.register(
                "search_memory", search_memory,
                "Semantic search over past agent reflections and successful fixes.",
                parameters={
                    "query": {
                        "type": "string",
                        "description": "Natural-language search query",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default 5)",
                    },
                },
                required=["query"],
            )
            self.register(
                "store_reflection", store_reflection,
                "Saves an agent insight or fix into long-term hippocampus memory.",
                parameters={
                    "mission_id": {
                        "type": "string",
                        "description": "Current mission identifier",
                    },
                    "reflection_type": {
                        "type": "string",
                        "description": "Type: fix | insight | pattern | architecture | security_finding",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full content to store",
                    },
                },
            )

        if organs.sensory is not None:
            sensory = organs.sensory

            async def get_vision_report(hours_back: int = 24) -> str:
                """
                Returns a PostHog UX health report — rage clicks, conversions,
                and health ratio for the specified time window.
                """
                return await sensory.generate_vision_report(hours_back=hours_back)

            self.register(
                "get_vision_report", get_vision_report,
                "Generates a PostHog UX health report from session events.",
                parameters={"hours_back": {
                    "type": "integer",
                    "description": "Look-back window in hours (default 24)",
                }},
                required=[],
            )
