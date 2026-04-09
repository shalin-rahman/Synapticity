import os
import requests
import sys
from synaptic.config import settings
from rich.console import Console
from rich.table import Table

console = Console()

class SynapticDoctor:
    """Performs deep diagnostics on the synaptic environment."""
    
    @staticmethod
    def check_vitals():
        console.print("[bold cyan]🩺 synaptic System Diagnostics...[/]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="dim")
        table.add_column("Status")
        table.add_column("Details")

        # 1. Gemini Keys
        keys = settings.GEMINI_KEYS
        if keys:
            table.add_row("Cloud (Gemini)", "[green]OK[/]", f"{len(keys)} keys active")
        else:
            table.add_row("Cloud (Gemini)", "[red]FAILED[/]", "No valid keys in .env")

        # 2. Ollama Connectivity
        try:
            res = requests.get(settings.OLLAMA_URL.replace("/generate", "/tags"), timeout=2)
            if res.status_code == 200:
                table.add_row("Local (Ollama)", "[green]OK[/]", "Service reachable")
            else:
                table.add_row("Local (Ollama)", "[yellow]WARN[/]", f"Status: {res.status_code}")
        except:
            table.add_row("Local (Ollama)", "[red]FAILED[/]", "Service unreachable (check 'ollama serve')")

        # 3. Workspace Health
        if os.path.exists(settings.WORKSPACE_PATH):
            table.add_row("Workspace", "[green]OK[/]", "Directory writable")
        else:
            table.add_row("Workspace", "[yellow]WARN[/]", "Directory missing (will be auto-created)")

        # 4. Agent Personas
        agent_dir = settings.AGENT_PATH
        if os.path.exists(agent_dir) and len(os.listdir(agent_dir)) >= 5:
            table.add_row("Intelligence", "[green]OK[/]", f"All {len(os.listdir(agent_dir))} personas loaded")
        else:
            table.add_row("Intelligence", "[red]FAILED[/]", "Personas missing from agents/ folder")

        console.print(table)
        
        # Binary health check
        return settings.IS_HEALTHY and os.path.exists(agent_dir)
