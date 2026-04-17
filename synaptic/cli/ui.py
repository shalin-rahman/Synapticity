"""Static UI renderers: dashboard and help panel."""
import os
import time
from rich.table import Table
from rich.panel import Panel
from synaptic.config import settings
from synaptic.cli.utils import console, load_state


def show_dashboard() -> None:
    """Renders the project overview dashboard."""
    table = Table(title="Project Dashboard", expand=True)
    table.add_column("ID",   style="cyan", no_wrap=True)
    table.add_column("Title",style="white")
    table.add_column("Status",       style="magenta")
    table.add_column("Verdict",      style="green")
    table.add_column("Last Updated", style="yellow")

    workspace = settings.WORKSPACE_PATH
    if os.path.exists(workspace):
        for mission in os.listdir(workspace):
            path = os.path.join(workspace, mission)
            if not os.path.isdir(path):
                continue
            title, verdict, status = "New Project", "Pending", "Initialized"
            state = load_state(mission)
            if state:
                title   = state.get("title", mission.replace("-", " ").title())
                verdict = state.get("verdict", "Pending")
                output_ok = os.path.exists(os.path.join(path, "output", "main.py"))
                status = "Completed" if output_ok else ("Planning" if state.get("specs") else "Initialized")
            last_sync = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path)))
            table.add_row(mission, title, status, verdict, last_sync)

    console.print(table)


def show_help() -> None:
    """Renders the help panel listing all CLI commands."""
    console.print(Panel(
        f"[bold cyan]Synapticity Framework (v{settings.VERSION})[/]\n"
        "[dim]Professional-grade collaborative software engineering.[/dim]"
    ))
    console.print("\n[bold]Usage Commands:[/]")
    commands = [
        ("dash",                       "View all projects and their current status"),
        ("stats",                      "View performance analytics and scorecards"),
        ("launch <id> <goal>",         "Start a new project development cycle"),
        ("resume <id>",                "Continue work on an existing project"),
        ("update <id> <goal>",         "Modify project goals and trigger a re-design"),
        ("remove <id>",                "Permanently delete a project from the workspace"),
        ("agent <id> <agent> <task>",  "Dispatch a specialist for a manual task"),
        ("audit <id>",                 "Review the project checklist and progress"),
        ("log <id>",                   "Open the project history and audit trail"),
        ("deploy <id>",                "Sync with GitHub and set up documentation"),
        ("review <id> <path> <goal>",  "Perform a code review or automated patch"),
        ("learn <id>",                 "Analyze project logs to update shared team knowledge"),
        ("ingest <type> <url> <name>", "Import project playbooks or specialist personas"),
        ("stress",                     "Benchmark system connectivity and performance"),
        ("doctor",                     "Check framework dependencies and configuration"),
        ("help",                       "Show this detailed help menu"),
    ]
    for cmd, desc in commands:
        console.print(f"  [green]{cmd:<28}[/] {desc}")
