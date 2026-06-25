"""
CLI Handler for ./sync idle-learn

  ./sync idle-learn              Start monitoring loop (Ctrl+C to stop)
  ./sync idle-learn --once       One idle-check + one replay, then exit
  ./sync idle-learn --dry-run    Show what would be replayed, no execution
  ./sync idle-learn --status     Print replay history and pending missions
  ./sync idle-learn --now        Force one replay immediately (skip idle check)
"""

import asyncio
import sys
from synaptic.cli.utils import console
from rich.table import Table


def handle_idle_learn() -> None:
    args = set(sys.argv[2:])

    if "--status" in args:
        _show_status()
        return

    dry_run = "--dry-run" in args
    force_now = "--now" in args
    once = "--once" in args or dry_run or force_now

    try:
        from synaptic.core.idle_learning import IdleLearningScheduler
        scheduler = IdleLearningScheduler()

        if force_now:
            asyncio.run(scheduler.run_now(dry_run=dry_run))
        else:
            asyncio.run(scheduler.run(once=once, dry_run=dry_run))

    except KeyboardInterrupt:
        console.print("\n[bold yellow][IDLE-LEARN][/] Stopped.")


def _show_status() -> None:
    from synaptic.core.idle_learning import IdleLearningScheduler
    scheduler = IdleLearningScheduler()
    data = scheduler.status()

    pending = data.get("pending", [])
    replay_log = data.get("replay_log", {}).get("replays", {})

    table = Table(title="Pending Failed Missions", show_lines=True)
    table.add_column("Mission ID", style="bold cyan")
    table.add_column("Phase")
    table.add_column("Attempts", justify="right")
    table.add_column("Last Outcome")
    table.add_column("Objective")
    if pending:
        for m in pending:
            table.add_row(
                m["mission_id"],
                m["phase"],
                str(m["attempts"]),
                m["last_outcome"],
                m["objective"][:50],
            )
    else:
        table.add_row("-", "-", "-", "-", "No pending missions")
    console.print(table)

    if replay_log:
        hist = Table(title="Replay History", show_lines=True)
        hist.add_column("Mission ID", style="bold")
        hist.add_column("Attempts", justify="right")
        hist.add_column("Last Outcome")
        hist.add_column("Last Attempted")
        for mid, info in replay_log.items():
            hist.add_row(
                mid,
                str(info.get("attempts", 0)),
                info.get("last_outcome", "-"),
                info.get("last_attempted", "-")[:19],
            )
        console.print(hist)
