"""
CLI Handler for the `tool` command.

Directly invokes any registered SynapticToolDispatcher tool from the terminal.
Useful for testing organ connectivity and skill retrieval without launching a full mission.

Usage
─────
    ./sync tool list_skills
    ./sync tool get_skill_content api-design
    ./sync tool search_memory "FastAPI authentication fix"
    ./sync tool get_vision_report 48
    ./sync tool organ_health_check
"""
import asyncio
import json
import sys

from rich.panel import Panel
from rich.syntax import Syntax

from synaptic.cli.utils import console


def handle_tool():
    """Invoke a registered Synapticity tool directly from the CLI."""
    args = sys.argv[2:]

    if not args or args[0] in ("-h", "--help"):
        _show_usage()
        return

    tool_name = args[0]
    tool_args = args[1:]

    console.print(
        f"[bold cyan][TOOL][/] Invoking: [bold]{tool_name}[/] "
        + (f"with args: {tool_args}" if tool_args else "(no args)")
    )

    try:
        result = asyncio.run(_dispatch(tool_name, tool_args))
        _render_result(result)
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[bold red][ERROR][/] {exc}")
        sys.exit(1)


async def _dispatch(tool_name: str, raw_args: list) -> str:
    """Builds the dispatcher, resolves arg types, and executes the tool."""
    from synaptic.core.tool_dispatcher import SynapticToolDispatcher
    from synaptic.core.skill_registry import SkillRegistry

    # Load skill registry and organs for full tool coverage
    skill_registry = SkillRegistry()

    organs = None
    try:
        from synaptic.organs import SynapticOrganInterface
        organs = SynapticOrganInterface()
    except Exception:
        pass  # Organs offline — still run builtin + skill tools

    dispatcher = SynapticToolDispatcher(
        skill_registry=skill_registry,
        organs=organs,
    )

    # Special command: list all available tools
    if tool_name == "list":
        return "Available tools:\n  " + "\n  ".join(dispatcher.tool_names)

    # Parse positional args — try JSON decode, fall back to string
    kwargs: dict = {}
    if raw_args:
        declarations = {d["name"]: d for d in dispatcher.get_function_declarations()}
        decl = declarations.get(tool_name)
        if decl:
            props = decl.get("parameters", {}).get("properties", {})
            param_names = list(props.keys())
            for i, val in enumerate(raw_args):
                if i < len(param_names):
                    name = param_names[i]
                    prop_type = props[name].get("type", "string")
                    kwargs[name] = _coerce(val, prop_type)
        else:
            kwargs = {}  # unknown tool — pass no args, let dispatcher report the error

    return await dispatcher.execute(tool_name, kwargs)


def _coerce(value: str, type_hint: str):
    """Coerce a CLI string argument to the declared JSON schema type."""
    if type_hint == "integer":
        try:
            return int(value)
        except ValueError:
            return value
    if type_hint == "boolean":
        return value.lower() in ("true", "1", "yes")
    if type_hint == "number":
        try:
            return float(value)
        except ValueError:
            return value
    # Try JSON for objects/arrays, fall back to raw string
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return value


def _render_result(result: str) -> None:
    """Pretty-prints the tool result — detects JSON and syntax-highlights it."""
    try:
        parsed = json.loads(result)
        pretty = json.dumps(parsed, indent=2)
        console.print(
            Panel(
                Syntax(pretty, "json", theme="monokai"),
                title="[bold green][TOOL] Result[/]",
                border_style="green",
            )
        )
    except (json.JSONDecodeError, ValueError):
        console.print(
            Panel(result, title="[bold green][TOOL] Result[/]", border_style="green")
        )


def _show_usage() -> None:
    console.print(
        Panel(
            "[bold]Usage:[/] ./sync tool [bold]<tool_name>[/] [args...]\n\n"
            "[dim]Examples:[/]\n"
            "  ./sync tool list\n"
            "  ./sync tool list_skills\n"
            "  ./sync tool get_skill_content api-design\n"
            "  ./sync tool search_memory \"FastAPI auth fix\" 3\n"
            "  ./sync tool get_vision_report 48\n"
            "  ./sync tool organ_health_check\n\n"
            "[dim]Run [bold]./sync tool list[/] to see all available tools.[/]",
            title="[TOOL] Synapticity Tool Invoker",
            border_style="cyan",
        )
    )
