import sys
import os
import io
import time

# Permanent fix for Windows terminal emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add root to path so we can import synaptic
sys.path.append(os.getcwd())

from synaptic.core.agent_runner import AgentRunner
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.config import settings
from rich.console import Console

console = Console()

def verify_system():
    console.print("\n[bold cyan][TEST] Synaptic Connectivity & Priority Test[/]\n")
    
    cloud = GeminiAdapter()
    local = OllamaAdapter()
    
    # We want to verify that Local is picked first
    runner = AgentRunner(local, settings.AGENT_PM, fallback_model=cloud)
    
    console.print(f"Primary Model: [bold]{type(runner.model).__name__}[/]")
    console.print(f"Fallback Model: [bold]{type(runner.fallback_model).__name__}[/]\n")
    
    if type(runner.model) is not OllamaAdapter:
        console.print("[red][FAIL] ERROR: Model priority is incorrect! Ollama should be primary.[/]")
        return False

    console.print("[LAUNCH] Initiating Test Prompt to verify activity display...")
    try:
        # A simple prompt that should return quickly
        response = runner.execute("Describe the mission of building a secure vault in one sentence.")
        console.print(f"\n[bold green][OK] Agent logic is working![/]")
        console.print(f"Agent Response: {response[:100]}...")
        return True
    except Exception as e:
        console.print(f"\n[bold red][FAIL] System Test Failed:[/] {e}")
        return False

if __name__ == "__main__":
    success = verify_system()
    sys.exit(0 if success else 1)
