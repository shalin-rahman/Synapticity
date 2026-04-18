"""Mission lifecycle CLI handlers: launch, resume, update, remove, agent."""
import os
import sys
import shutil
from rich.panel import Panel
import synaptic
from synaptic.config import settings
from synaptic.cli.utils import console, sanitize_id, require_args
from synaptic.core.mission_state import MissionStateManager


def handle_launch() -> None:
    if not require_args(4, "Usage: python main.py launch <mission_id> '<goal>'"):
        return
    synaptic.launch(sanitize_id(sys.argv[2]), " ".join(sys.argv[3:]))


def handle_resume() -> None:
    if not require_args(3, "Usage: python main.py resume <mission_id>"):
        return
    synaptic.resume(sanitize_id(sys.argv[2]))


def handle_update() -> None:
    if not require_args(4, "Usage: python main.py update <mission_id> '<new_goal>'"):
        return
    mission_id = sanitize_id(sys.argv[2])
    new_goal   = " ".join(sys.argv[3:])
    workspace  = os.path.join(settings.WORKSPACE_PATH, mission_id)

    if not os.path.exists(workspace):
        console.print(f"[red]Error: Mission {mission_id} not found.[/]")
        return

    state_mgr = MissionStateManager(workspace)
    state = state_mgr.load()
    if not state or state.get("phase") == "START":
        console.print(f"[red]Error: Mission {mission_id} state missing or uninitialized.[/]")
        return

    old_objective = state.get("objective", "None")
    state.update({"objective": new_goal, "specs": None, "code": None, "phase": "UPDATED"})
    state_mgr.save(state)

    console.print(Panel(
        f"[bold yellow]Project Update Summary[/]\n\n"
        f"[bold]Project:[/] {mission_id}\n"
        f"[dim]Previous Objective:[/] {old_objective}\n"
        f"[bold green]New Objective:[/] {new_goal}\n\n"
        f"[dim]System Action:[/] Existing plans and code have been cleared. "
        f"History has been retained. Ready to re-start the planning phase.",
        title="Project Updated",
        border_style="yellow"
    ))
    synaptic.resume(mission_id)


def handle_remove() -> None:
    if not require_args(3, "Usage: python main.py remove <mission_id>"):
        return
    mission_id = sanitize_id(sys.argv[2])
    workspace  = os.path.join(settings.WORKSPACE_PATH, mission_id)
    if not os.path.exists(workspace):
        console.print(f"[red]Error: Mission {mission_id} not found in workspace.[/]")
        return
    shutil.rmtree(workspace)
    console.print(Panel(
        f"[bold red]Project Deleted[/]\n\n"
        f"[bold]Project:[/] {mission_id}\n"
        f"[dim]Action:[/] Successfully removed the project directory and all associated state files.",
        title="Removal Complete",
        border_style="red"
    ))


def handle_agent() -> None:
    if not require_args(5, "Usage: python main.py agent <mission_id> <agent_name> '<task>'\n[dim]Agents: pm, swe, tester, oncall, writer[/]"):
        return
    synaptic.dispatch(sanitize_id(sys.argv[2]), sys.argv[3].lower(), " ".join(sys.argv[4:]))
