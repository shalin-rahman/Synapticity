import time
import asyncio
from rich.console import Console
from rich.table import Table
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter

console = Console()

async def run_stress_test():
    """Validates multi-account rotation and burst capacity for synaptic.
    
    Uses the official GeminiAdapter.generate() path to respect SLEEP_BUFFER
    and rate-limit rotation logic, producing a realistic throughput benchmark.
    """
    adapter = GeminiAdapter()
    keys = settings.GEMINI_KEYS
    
    if not keys:
        console.print("[bold red]Critical Error: No GEMINI_KEY_X found in .env.[/]")
        return

    console.print(f"[bold cyan]Benchmarking synaptic Pool ({len(keys)} Accounts)...[/]")
    console.print(f"[INFO] SLEEP_BUFFER={settings.SLEEP_BUFFER}s | Model={settings.GEMINI_MODEL}")
    results = []

    for i, _ in enumerate(keys):
        console.print(f"[TEST] Testing Account {i+1}...")
        count = 0
        start_time = time.time()
        
        # Burst test: fire requests via the official adapter path
        for _ in range(5):
            try:
                await adapter.generate(
                    system_instruction="You are a ping responder.",
                    prompt="ping"
                )
                count += 1
                console.print(f"  [green][OK][/] Burst {count} success", end="\r")
            except Exception as e:
                console.print(f"\n  [red][FAIL][/] Account {i+1} saturated: {e}")
                break
        
        elapsed = time.time() - start_time
        results.append({
            "account": i+1,
            "requests": count,
            "elapsed": round(elapsed, 2)
        })
        
        console.print(f"\n  Account {i+1} benchmarked in {round(elapsed, 2)}s.")
        await adapter.rotate()

    # Summary
    table = Table(title="[STATS] synaptic Pool Performance Summary")
    table.add_column("Account Pool", style="cyan")
    table.add_column("Throughput (Req)", style="green")
    table.add_column("Response Latency", style="yellow")

    for res in results:
        table.add_row(f"Acc {res['account']}", str(res['requests']), f"{res['elapsed']}s")

    console.print(table)

def main():
    asyncio.run(run_stress_test())

if __name__ == "__main__":
    main()

