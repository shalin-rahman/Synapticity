"""
CLI Handler for the `estimate` command.
Reads a PDF or DOCX document and produces a professional estimation report.
"""

import asyncio
import os
import sys
from synaptic.core.estimation_engine import EstimationEngine
from synaptic.config import settings
from synaptic.cli.utils import console
from rich.panel import Panel
from rich.table import Table


def handle_estimate():
    """Handle the estimate command: parse document and generate estimation report."""
    args = sys.argv[2:]

    if len(args) < 1:
        console.print(Panel(
            "[bold red]Usage:[/] ./sync estimate <document_path> [project_name]\n\n"
            "[dim]Examples:[/]\n"
            "  ./sync estimate docs/requirements.pdf\n"
            "  ./sync estimate specs.docx 'E-Commerce Platform'",
            title="[ERROR] Estimate Command",
            border_style="red"
        ))
        sys.exit(1)

    document_path = args[0]
    project_name = args[1] if len(args) > 1 else None

    if not os.path.exists(document_path):
        console.print(f"[bold red]Error:[/] Document not found: {document_path}")
        sys.exit(1)

    console.print(f"[bold cyan][ESTIMATE][/] Analyzing document: {document_path}")

    try:
        engine = EstimationEngine()
        estimate = engine.prepare_estimate(document_path, project_name)

        # AI refinement — enhance the heuristic PERT with LLM reasoning
        estimate = _try_ai_refinement(engine, estimate)

        # Display summary in terminal
        _display_estimate_summary(estimate)

        # Save to workspace
        output_dir = os.path.join(settings.WORKSPACE_PATH, "estimates", estimate.project_name.replace(" ", "-").lower())
        engine.save_estimate(estimate, output_dir)

        console.print(f"\n[bold green][OK][/] Estimation report saved to: {output_dir}")
        console.print(f"  - {output_dir}/ESTIMATION_REPORT.md")
        console.print(f"  - {output_dir}/estimate.json")

    except ImportError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("[dim]Install required dependencies:[/]")
        console.print("  pip install pdfplumber python-docx")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to generate estimate: {e}")
        sys.exit(1)


def _try_ai_refinement(engine, estimate):
    """Attempt LLM-based PERT refinement; silently skip on any failure."""
    doc = engine._last_doc
    if not doc:
        return estimate

    try:
        from synaptic.core.intelligence_router import IntelligenceRouter
        router = IntelligenceRouter()
        primary, _ = router.resolve()
    except Exception:
        return estimate

    console.print("[dim][ESTIMATE] Running AI refinement...[/]")
    try:
        estimate = asyncio.run(engine.refine_with_ai(estimate, doc, primary))
        if "[AI-Refined" in estimate.risk_assessment:
            confidence = "medium"
            import re
            m = re.search(r"confidence:\s*(\w+)", estimate.risk_assessment)
            if m:
                confidence = m.group(1)
            console.print(f"[bold green][AI][/] Refinement applied (confidence: {confidence})")
    except Exception:
        pass

    return estimate


def _display_estimate_summary(estimate):
    """Display a rich summary of the estimate in the terminal."""
    console.print(Panel(
        f"[bold]{estimate.project_name}[/]\n"
        f"[dim]Source:[/] {estimate.source_document}\n"
        f"[dim]Generated:[/] {estimate.generated_at}",
        title="[ESTIMATE] Project Estimation Report",
        border_style="cyan"
    ))

    # PERT Summary Table
    table = Table(title="Effort Estimate (PERT)")
    table.add_column("Metric", style="bold")
    table.add_column("Hours", justify="right")
    table.add_column("Days (8h)", justify="right")
    table.add_column("Weeks (5d)", justify="right")

    table.add_row("Optimistic", f"{estimate.total_optimistic:.1f}h", f"{estimate.total_optimistic/8:.1f}d", f"{estimate.total_optimistic/40:.1f}w")
    table.add_row("Likely", f"{estimate.total_likely:.1f}h", f"{estimate.total_likely/8:.1f}d", f"{estimate.total_likely/40:.1f}w")
    table.add_row("Pessimistic", f"{estimate.total_pessimistic:.1f}h", f"{estimate.total_pessimistic/8:.1f}d", f"{estimate.total_pessimistic/40:.1f}w")
    table.add_row("Expected (PERT)", f"[bold]{estimate.total_expected:.1f}h[/]", f"{estimate.total_expected/8:.1f}d", f"{estimate.total_expected/40:.1f}w")

    console.print(table)

    console.print(f"\n[dim]95% Confidence Interval:[/] {estimate.confidence_95_range[0]:.1f}h - {estimate.confidence_95_range[1]:.1f}h")

    # Components summary
    console.print(f"\n[bold]Components:[/] {len(estimate.components)}")
    for comp in estimate.components:
        total_hours = sum(t.expected_hours for t in comp.tasks)
        console.print(f"  - {comp.name} ({comp.type}): {total_hours:.1f}h expected, {len(comp.tasks)} tasks")

    # Risk summary
    if estimate.risk_assessment:
        console.print(f"\n[bold]Risk Assessment:[/]")
        console.print(estimate.risk_assessment)

    # Team
    console.print(f"\n[bold]Recommended Team:[/]")
    for role in estimate.recommended_team:
        console.print(f"  - {role}")

