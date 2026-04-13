"""CLI handler for project reflection and knowledge synthesis."""
import sys
from synaptic.cli.utils import console, sanitize_id, require_args

def handle_learn() -> None:
    """
    Usage: ./sync learn <mission_id>

    Analyzes project history to improve future engineering standards.
    """
    if not require_args(3, "Usage: python main.py learn <mission_id>"):
        return

    mission_id = sanitize_id(sys.argv[2])
    
    from synaptic.core.self_learning import ReflectionEngine
    engine = ReflectionEngine()
    
    lessons = engine.analyze(mission_id)
    
    from rich.panel import Panel
    console.print(Panel(
        lessons, 
        title=f"Lessons Learned from {mission_id}", 
        border_style="cyan"
    ))
