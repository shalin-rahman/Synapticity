"""Static UI renderers: dashboard and help panel."""
import os
import time
from rich.table import Table
from rich.panel import Panel
from synaptic.config import settings
from synaptic.cli.utils import console, load_state


def show_dashboard() -> None:
    """Renders the mission overview dashboard."""
    table = Table(title="[SYS] Synaptic Command Center", expand=True)
    table.add_column("Mission ID",   style="cyan", no_wrap=True)
    table.add_column("Mission Title",style="white")
    table.add_column("Status",       style="magenta")
    table.add_column("Live Verdict", style="green")
    table.add_column("Last Sync",    style="yellow")

    workspace = settings.WORKSPACE_PATH
    if os.path.exists(workspace):
        for mission in os.listdir(workspace):
            path = os.path.join(workspace, mission)
            if not os.path.isdir(path):
                continue
            title, verdict, status = "Unknown Mission", "[dim]Pending[/]", "[DIR] New"
            state = load_state(mission)
            if state:
                title   = state.get("title", mission.replace("-", " ").title())
                verdict = state.get("verdict", "[dim]Pending[/]")
                output_ok = os.path.exists(os.path.join(path, "output", "main.py"))
                status = "[DONE] Completed" if output_ok else ("[AI] Planning" if state.get("specs") else "[DIR] New")
            last_sync = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path)))
            table.add_row(mission, title, status, verdict, last_sync)

    console.print(table)


def show_help() -> None:
    """Renders the help panel listing all CLI commands."""
    console.print(Panel(
        "[bold cyan]The State of Intelligent Connection (v3.0)[/]\n"
        "[dim]Principal-Grade Autonomous Software Engineering.[/dim]"
    ))
    console.print("\n[bold]Commands:[/]")
    commands = [
        ("dash",                       "View all mission titles and live status"),
        ("launch <id> <goal>",         "Start a new mission"),
        ("resume <id>",                "Resume a paused mission"),
        ("update <id> <goal>",         "Update a mission goal and trigger re-gen"),
        ("remove <id>",                "Purge a mission from the workspace entirely"),
        ("agent <id> <agent> <task>",  "Dispatch a solo agent for a specific task"),
        ("audit <id>",                 "View the detailed task checklist for a mission"),
        ("log <id>",                   "Read the historical mission markdown audit trail"),
        ("deploy <id>",                "Build Git repo and deploy mission to GitHub autonomously"),
        ("review <id> <path> \"<goal>\"","Review & optionally patch an existing project (add --apply to modify)"),
        ("ingest <type> <url> <name>", "Pull a remote 'skill' or 'agent' playbook natively"),
        ("stress",                     "Benchmark API accounts"),
        ("doctor",                     "Diagnose system health"),
        ("admin",                      "Secure gateway for framework self-management"),
        ("help",                       "Show this help message"),
    ]
    for cmd, desc in commands:
        console.print(f"  [green]{cmd}[/]  - {desc}")
