import time
from rich.console import Console
from rich.table import Table
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter

console = Console()

def run_stress_test():
    """Validates multi-account rotation and burst capacity for synaptic."""
    adapter = GeminiAdapter()
    keys = settings.GEMINI_KEYS
    
    if not keys:
        console.print("[bold red]Critical Error: No GEMINI_KEY_X found in .env.[/]")
        return

    console.print(f"[bold cyan]Benchmarking synaptic Pool ({len(keys)} Accounts)...[/]")
    results = []

    for i, _ in enumerate(keys):
        console.print(f"🧪 Testing Account {i+1}...")
        count = 0
        start_time = time.time()
        
        # Burst test: fire rapid low-token requests
        for _ in range(5):
            try:
                adapter.client.models.generate_content(
                    model=settings.GEMINI_MODEL, 
                    contents="ping"
                )
                count += 1
                console.print(f"  [green]✔[/] Burst {count} success", end="\r")
            except Exception as e:
                console.print(f"\n  [red]✘[/] Account {i+1} saturated: {e}")
                break
        
        elapsed = time.time() - start_time
        results.append({
            "account": i+1,
            "requests": count,
            "elapsed": round(elapsed, 2)
        })
        
        console.print(f"\n  Account {i+1} benchmarked in {round(elapsed, 2)}s.")
        adapter.rotate()

    # Summary
    table = Table(title="📈 synaptic Pool Performance Summary")
    table.add_column("Account Pool", style="cyan")
    table.add_column("Throughput (Req)", style="green")
    table.add_column("Response Latency", style="yellow")

    for res in results:
        table.add_row(f"Acc {res['account']}", str(res['requests']), f"{res['elapsed']}s")

    console.print(table)

if __name__ == "__main__":
    run_stress_test()
