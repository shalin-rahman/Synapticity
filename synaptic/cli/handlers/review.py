"""Review CLI handler — external project review and modification."""
import sys
import os
from rich.markdown import Markdown
from synaptic.cli.utils import console, sanitize_id, require_args


def handle_review() -> None:
    """
    Usage: ./sync review <mission_id> <project_path> "<goal>" [--apply]

    Crawls the project at <project_path>, dispatches the agent team for a
    structured review, and saves REVIEW_REPORT.md into the mission workspace.
    Pass --apply to write agent-suggested FILE_PATCH blocks back to disk.
    """
    if not require_args(5, "Usage: python main.py review <mission_id> <project_path> \"<goal>\" [--apply]"):
        return

    mission_id   = sanitize_id(sys.argv[2])
    project_path = sys.argv[3]
    apply_flag   = "--apply" in sys.argv
    # Goal is everything between argv[4] and the optional --apply flag
    goal_parts   = [a for a in sys.argv[4:] if a != "--apply"]
    goal         = " ".join(goal_parts)

    if not os.path.isdir(project_path):
        console.print(f"[bold red][FAIL][/] Path does not exist or is not a directory: {project_path}")
        return

    if apply_flag:
        console.print("[yellow][PATCH] Modification mode enabled — agent patches will be written to disk.[/]")

    from synaptic.core.project_review_engine import ProjectReviewEngine
    engine = ProjectReviewEngine()
    report = engine.review(project_path, goal, mission_id, apply_changes=apply_flag)

    console.print("\n")
    console.print(Markdown(report))
