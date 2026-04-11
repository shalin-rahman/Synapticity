"""Shared utilities consumed by all CLI handler modules."""
import os
import json
import sys
from rich.console import Console
from synaptic.config import settings

console = Console()


def sanitize_id(m_id: str) -> str:
    """Strips shell-injected prefixes from a mission ID."""
    return m_id.replace("./sync", "").replace(".bat", "").strip("/")


def require_args(count: int, usage: str) -> bool:
    """Prints usage and returns False when argv is too short."""
    if len(sys.argv) < count:
        console.print(f"[red]{usage}[/]")
        return False
    return True


def load_state(mission_id: str) -> dict | None:
    """Loads state.json for a mission. Returns None if missing."""
    path = os.path.join(settings.WORKSPACE_PATH, mission_id, settings.STATE_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(mission_id: str, state: dict) -> None:
    """Persists state.json for a mission."""
    path = os.path.join(settings.WORKSPACE_PATH, mission_id, settings.STATE_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)
