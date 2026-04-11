import sys
import io

# Permanent fix for Windows terminal encoding (must be before any other import)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
    except:
        pass

from synaptic.cli import COMMAND_REGISTRY
from synaptic.cli.ui import show_help
from synaptic.cli.utils import console
from synaptic.utils.exceptions import SynapticError


def main() -> None:
    if len(sys.argv) < 2:
        show_help()
        return

    action  = sys.argv[1].lower()
    handler = COMMAND_REGISTRY.get(action)

    if handler:
        handler()
    else:
        console.print(f"[red]Unknown command: '{action}'. Run [bold]./sync help[/] for usage.[/]")


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
        sys.exit(1)
