import sys
import os
import json
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import synaptic
from synaptic.utils.exceptions import SynapticError
from synaptic.utils.doctor import SynapticDoctor
import io

# Permanent fix for Windows terminal emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

console = Console()

def show_dashboard():
    """Displays the Synaptic Command Center dashboard."""
    table = Table(title="🤖 Synaptic Command Center", expand=True)
    table.add_column("Mission ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Security", style="green")
    table.add_column("Last Sync", style="yellow")

    workspace = "workspace"
    if os.path.exists(workspace):
        for mission in os.listdir(workspace):
            path = os.path.join(workspace, mission)
            if os.path.isdir(path):
                specs_exists = os.path.exists(os.path.join(path, "specs.json"))
                output_exists = os.path.exists(os.path.join(path, "output", "main.py"))
                
                status = "🏁 Completed" if output_exists else ("🧠 Planning" if specs_exists else "📂 New")
                security = "🔒 Verified" if output_exists else "❔ Pending"
                last_sync = time.ctime(os.path.getmtime(path))
                
                table.add_row(mission, status, security, last_sync)
    
    console.print(table)
    
    # Usage Stats
    log_file = "usage_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            data = json.load(f)
        today = time.strftime("%Y-%m-%d")
        calls = data.get(today, 0)
        console.print(f"\n[bold green]Daily Requests:[/] {calls}/5000")

def show_help():
    """Displays the Synaptic Command Center help panel."""
    console.print(Panel("[bold cyan]The State of Intelligent Connection (v2.0)[/]\n[dim]Powering autonomous software development missions.[/dim]"))
    console.print("\n[bold]Commands:[/]")
    console.print("  [green]dash[/]                - View all missions")
    console.print("  [green]launch <id> <goal>[/]  - Start a new mission")
    console.print("  [green]resume <id>[/]         - Resume a paused mission")
    console.print("  [green]stress[/]              - Benchmark API accounts")
    console.print("  [green]doctor[/]              - Diagnose system health")
    console.print("  [green]help[/]                - Show this help message")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    action = sys.argv[1].lower()

    if action == "dash":
        show_dashboard()
    elif action == "doctor":
        SynapticDoctor.check_vitals()
    elif action == "help":
        show_help()
    elif action == "launch":
        if len(sys.argv) < 4:
            console.print("[red]Usage: python main.py launch <mission_id> '<goal>'[/]")
            return
        mission_id = sys.argv[2]
        goal = " ".join(sys.argv[3:])
        synaptic.launch(mission_id, goal)
    elif action == "resume":
        if len(sys.argv) < 3:
            console.print("[red]Usage: python main.py resume <mission_id>[/]")
            return
        synaptic.resume(sys.argv[2])
    elif action == "stress":
        # Import stress test logic or call script
        import subprocess
        subprocess.run([sys.executable, "stress_test.py"])
    else:
        console.print(f"[red]Unknown command: {action}[/]")

if __name__ == "__main__":
    try:
        main()
    except SynapticError as ne:
        console.print(f"\n[bold red]Synaptic Error:[/] {ne}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Mission aborted by operator.[/]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Critical System Failure:[/] {e}")
        # Optionally show traceback in debug mode
        sys.exit(1)
