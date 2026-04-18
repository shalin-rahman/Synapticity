"""Observability CLI handlers: audit task list and mission log viewer."""
import os
import sys
from rich.table import Table
from rich.markdown import Markdown
from synaptic.config import settings
from synaptic.cli.utils import console, sanitize_id, require_args
from synaptic.core.mission_state import MissionStateManager


def handle_audit() -> None:
    if not require_args(3, "Usage: python main.py audit <mission_id>"):
        return
    mission_id = sanitize_id(sys.argv[2])
    workspace  = os.path.join(settings.WORKSPACE_PATH, mission_id)

    if not os.path.exists(workspace):
        console.print(f"[red]Error: Mission {mission_id} not found.[/]")
        return

    state_mgr = MissionStateManager(workspace)
    state = state_mgr.load()
    if not state:
        console.print(f"[red]No tasks recorded for {mission_id}.[/]")
        return

    table = Table(title=f"[AUDIT] Mission Audit: {mission_id}", expand=True)
    table.add_column("Agent / Role",   style="cyan")
    table.add_column("Task Objective", style="white")
    table.add_column("Timestamp",      style="dim")
    table.add_column("Status",         style="green")

    for entry in state.get("history", []):
        table.add_row(
            entry.get("role", "Unknown").upper(),
            entry.get("thought", ""),
            entry.get("timestamp", ""),
            "[OK] Completed"
        )

    phase = state.get("phase", "START")
    if phase in ("START", "UPDATED"):
        table.add_row("PRODUCT-MANAGER",   "Drafting Architectural Specs",   "Pending", "[PENDING] In Queue")
    if phase in ("START", "UPDATED", "PLANNED"):
        table.add_row("SOFTWARE-ENGINEER", "Synthesizing Source Code",       "Pending", "[PENDING] In Queue")
    if phase not in ("COMPLETED", "VERIFIED"):
        table.add_row("TESTER & ONCALL",   "Running Healing Loop & Scans",  "Pending", "[PENDING] In Queue")
    if phase != "COMPLETED":
        table.add_row("WRITER",            "Generating Technical Docs",     "Pending", "[PENDING] In Queue")

    console.print(table)


def handle_log() -> None:
    if not require_args(3, "Usage: python main.py log <mission_id>"):
        return
    mission_id = sanitize_id(sys.argv[2])
    log_path   = os.path.join(settings.WORKSPACE_PATH, mission_id, "MISSION_LOG.md")

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            console.print(Markdown(f.read()))
    else:
        console.print(f"[bold red][FAIL][/] No mission log found for '{mission_id}' at {log_path}")
