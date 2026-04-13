from synaptic.core.analytics import PerformanceAnalytics
from synaptic.cli.utils import console
from rich.panel import Panel

def handle_stats():
    """CLI handler for displaying project performance metrics."""
    analytics = PerformanceAnalytics()
    report = analytics.get_summary_report()
    
    console.print(Panel(
        report,
        title="[bold cyan]Performance Scorecard[/]",
        border_style="magenta",
        expand=False
    ))
