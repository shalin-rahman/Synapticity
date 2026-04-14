"""
HITL Approval Gate — interactive mission checkpoint prompts.
Single Responsibility: owns all human-in-the-loop gating logic.
"""
from synaptic.config import settings


class ApprovalGate:
    """Prompts the operator to authorize each major mission milestone."""

    def request(self, milestone_name: str, current_phase: str) -> None:
        """Shows a rich briefing panel and blocks until operator approves or aborts."""
        if not settings.INTERACTIVE_MODE:
            return

        from rich.panel import Panel
        from rich.console import Console
        Console().print(Panel(
            f"[bold green][OK] {milestone_name} COMPLETED[/]\n\n"
            f"[dim]Current Phase:[/] [cyan]{current_phase}[/]\n"
            f"[dim]Next Objective:[/] Initiating subsequent intelligence cycle...",
            title="[SEC] Synaptic Mission Briefing",
            border_style="green",
            expand=False
        ))

        choice = input("\n[LAUNCH] Press [ENTER] to authorize the next phase, or 'q' to abort: ").lower()
        if choice == "q":
            print("[HALT] Mission manually aborted by operator.")
            raise SystemExit(0)
        print()
