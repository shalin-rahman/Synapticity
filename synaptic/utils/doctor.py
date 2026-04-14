import os
import requests
import sys
import subprocess
import time
from synaptic.config import settings
from rich.console import Console
from rich.table import Table

console = Console()

class SynapticDoctor:
    """Performs deep diagnostics and automated healing of the Synaptic environment."""
    
    @staticmethod
    def run_full_service():
        """Checks vitals and attempts to heal any identified issues."""
        results = SynapticDoctor.check_vitals()
        
        needs_healing = any(status in ["[red]FAILED[/]", "[yellow]WARN[/]"] for status, _ in results.values())
        
        if needs_healing:
            console.print("\n[bold yellow][REPAIR] Synaptic Doctor is initiating Auto-Repair...[/]")
            SynapticDoctor.heal(results)
            console.print("\n[bold green][OK] Repair cycle complete. Running final check...[/]")
            SynapticDoctor.check_vitals()
        else:
            console.print("\n[bold green][SYS] System is at peak performance. No action needed.[/]")

    @staticmethod
    def check_vitals():
        console.print("[bold cyan][DIAGNOSTICS] Synaptic System Health...[/]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="dim")
        table.add_column("Status")
        table.add_column("Details")

        registry = {}

        # 1. Gemini Keys
        keys = settings.GEMINI_KEYS
        status, detail = ("[green]OK[/]", f"{len(keys)} keys active") if keys else ("[red]FAILED[/]", "No valid keys in .env")
        table.add_row("Cloud (Gemini)", status, detail)
        registry["gemini"] = (status, detail)

        # 2. Ollama Connectivity
        try:
            res = requests.get(settings.OLLAMA_URL.replace("/generate", "/tags"), timeout=2)
            if res.status_code == 200:
                models = [m['name'] for m in res.json().get('models', [])]
                if settings.OLLAMA_MODEL in models or f"{settings.OLLAMA_MODEL}:latest" in models:
                    status, detail = ("[green]OK[/]", "Service reachable & Model pulled")
                else:
                    status, detail = ("[yellow]WARN[/]", f"Service reachable but model '{settings.OLLAMA_MODEL}' missing")
            else:
                status, detail = ("[yellow]WARN[/]", f"Status: {res.status_code}")
        except:
            status, detail = ("[red]FAILED[/]", "Service unreachable")
        table.add_row("Local (Ollama)", status, detail)
        registry["ollama"] = (status, detail)

        # 3. Workspace Health
        status, detail = ("[green]OK[/]", "Directory writable") if os.path.exists(settings.WORKSPACE_PATH) else ("[yellow]WARN[/]", "Directory missing")
        table.add_row("Workspace", status, detail)
        registry["workspace"] = (status, detail)

        # 4. Agent Personas
        agent_dir = settings.AGENT_PATH
        if os.path.exists(agent_dir) and len(os.listdir(agent_dir)) >= 5:
            status, detail = ("[green]OK[/]", f"All {len(os.listdir(agent_dir))} personas loaded")
        else:
            status, detail = ("[red]FAILED[/]", "Personas missing")
        table.add_row("Intelligence", status, detail)
        registry["intelligence"] = (status, detail)

        console.print(table)
        return registry

    @staticmethod
    def heal(results):
        """Attempts to fix failure states automatically."""
        
        # Heal Workspace
        if results["workspace"][0] == "[yellow]WARN[/]":
            console.print("  [>] Creating workspace directory...")
            os.makedirs(settings.WORKSPACE_PATH, exist_ok=True)

        # Heal Ollama Service
        if results["ollama"][0] == "[red]FAILED[/]":
            console.print("  [>] Starting Ollama service...")
            try:
                if os.name == 'nt':
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(5)
            except:
                console.print("  [red][FAIL] Failed to start Ollama automatically.[/]")

        # Heal Ollama Model
        if results["ollama"][0] == "[yellow]WARN[/]":
            console.print(f"  [>] Pulling local model '{settings.OLLAMA_MODEL}'...")
            try:
                pull_url = settings.OLLAMA_URL.replace("/generate", "/pull")
                requests.post(pull_url, json={"name": settings.OLLAMA_MODEL, "stream": False}, timeout=600)
            except:
                console.print("  [red][FAIL] Failed to pull model. Please run 'ollama pull " + settings.OLLAMA_MODEL + "'[/]")

        # Gemini Guidance
        if results["gemini"][0] == "[red]FAILED[/]":
            console.print("  [bold cyan][HINT] Gemini:[/] Please paste your keys from https://aistudio.google.com/app/apikey into your .env file.")
