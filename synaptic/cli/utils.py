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
