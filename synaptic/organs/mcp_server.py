"""
SynapticMCPServer — Model Context Protocol server for Synapticity organs.

Exposes hippocampus, sensory, and efferent organs as MCP tools so any
MCP-compatible client (Gemini via ClientSession, Claude Desktop, Cursor, etc.)
can call them by name.

Running standalone
──────────────────
    python -m synaptic.organs.mcp_server

Connecting Gemini to this server
─────────────────────────────────
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from google import genai

    server_params = StdioServerParameters(
        command="python",
        args=["-m", "synaptic.organs.mcp_server"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents="Search memory for 'FastAPI authentication fix'",
                config=genai.types.GenerateContentConfig(tools=[session]),
            )
"""
from __future__ import annotations

import asyncio
import json

from synaptic.utils.logger import synaptic_log


def _build_server():
    """
    Builds and returns the FastMCP server instance.
    Import is deferred so missing 'mcp' package only errors at startup,
    not when synaptic.organs is imported by other modules.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise ImportError(
            "The 'mcp' package is required for SynapticMCPServer. "
            "Install it with: pip install mcp"
        ) from exc

    from synaptic.organs.SaaS_Interface import SynapticOrganInterface

    organs = SynapticOrganInterface(
        enabled=["hippocampus", "sensory", "efferent"]
    )

    mcp = FastMCP(
        name="Synapticity",
        instructions=(
            "You are connected to the Synapticity neuromorphic framework. "
            "Use these tools to query long-term agent memory, analyse UX signals, "
            "and dispatch structured reports."
        ),
    )

    # ── Tool: search_memory ───────────────────────────────────────────────────

    @mcp.tool()
    async def search_memory(query: str, limit: int = 5) -> str:
        """
        Semantic search over past agent reflections and successful fixes
        stored in the Synapticity hippocampus (Supabase + pgvector).

        Returns the top matching entries with similarity scores.
        """
        if organs.hippocampus is None:
            return "[ERROR] Hippocampus organ not configured (check SUPABASE_URL / SUPABASE_ANON_KEY)"
        results = await organs.hippocampus.semantic_lookup(query, limit=limit)
        if not results:
            return "(no relevant memories found)"
        lines = []
        for r in results:
            lines.append(
                f"[{r.get('reflection_type','?')} | similarity={r.get('similarity',0):.2f}]\n"
                f"Mission: {r.get('mission_id','?')}\n"
                f"{r.get('content','')[:500]}"
            )
        return "\n\n---\n\n".join(lines)

    # ── Tool: store_reflection ────────────────────────────────────────────────

    @mcp.tool()
    async def store_reflection(
        mission_id: str,
        reflection_type: str,
        content: str,
        agent_name: str = "mcp_client",
    ) -> str:
        """
        Stores a new agent reflection into long-term hippocampus memory.

        reflection_type options: fix | insight | pattern | architecture | security_finding
        Returns the UUID of the created record.
        """
        if organs.hippocampus is None:
            return "[ERROR] Hippocampus organ not configured"
        row_id = await organs.hippocampus.store_reflection(
            mission_id=mission_id,
            agent_name=agent_name,
            reflection_type=reflection_type,
            content=content,
        )
        return f"Stored: {row_id}"

    # ── Tool: get_vision_report ───────────────────────────────────────────────

    @mcp.tool()
    async def get_vision_report(hours_back: int = 24) -> str:
        """
        Returns a PostHog UX health report — rage clicks, conversions, and
        the frustration/success health ratio for the specified time window.
        """
        if organs.sensory is None:
            return "[ERROR] Sensory organ not configured (check POSTHOG_PERSONAL_API_KEY)"
        return await organs.sensory.generate_vision_report(hours_back=hours_back)

    # ── Tool: send_report ────────────────────────────────────────────────────

    @mcp.tool()
    async def send_report(
        mission_id: str,
        to_email: str,
        summary: str,
    ) -> str:
        """
        Sends a mission completion report email via Resend.
        Returns the Resend email ID on success.
        """
        if organs.efferent_synapse is None:
            return "[ERROR] Efferent synapse not configured (check RESEND_API_KEY)"
        email_id = await organs.efferent_synapse.send_mission_report(
            mission_id=mission_id,
            to_email=to_email,
            summary=summary,
        )
        return f"Email sent: {email_id}"

    # ── Tool: organ_health_check ──────────────────────────────────────────────

    @mcp.tool()
    async def organ_health_check() -> str:
        """
        Returns the real-time connectivity status for all Synapticity organs.
        """
        status = await organs.health_check()
        return json.dumps(status, indent=2)

    return mcp


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Starts the MCP server over stdio (used by MCP clients / Gemini ClientSession)."""
    synaptic_log.info("[MCP] Starting SynapticMCPServer over stdio...")
    server = _build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
