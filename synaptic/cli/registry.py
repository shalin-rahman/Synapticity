"""Command registry mapping action strings to handler callables."""
from synaptic.cli.ui import show_dashboard, show_help
from synaptic.cli.handlers.mission import (
    handle_launch, handle_resume, handle_update, handle_remove, handle_agent
)
from synaptic.cli.handlers.observe import handle_audit, handle_log
from synaptic.cli.handlers.integration import (
    handle_deploy, handle_ingest, handle_stress, handle_admin
)
from synaptic.cli.handlers.review import handle_review
from synaptic.cli.handlers.learning import handle_learn
from synaptic.utils.doctor import SynapticDoctor

from synaptic.cli.handlers.stats import handle_stats

from synaptic.cli.handlers.estimate import handle_estimate
from synaptic.cli.handlers.tool import handle_tool
from synaptic.cli.handlers.idle_learn import handle_idle_learn

COMMAND_REGISTRY: dict[str, callable] = {
    "dash":         show_dashboard,
    "help":         show_help,
    "stats":        handle_stats,
    "doctor":       SynapticDoctor.run_full_service,
    "launch":       handle_launch,
    "resume":       handle_resume,
    "update":       handle_update,
    "remove":       handle_remove,
    "agent":        handle_agent,
    "audit":        handle_audit,
    "log":          handle_log,
    "deploy":       handle_deploy,
    "ingest":       handle_ingest,
    "stress":       handle_stress,
    "admin":        handle_admin,
    "review":       handle_review,
    "learn":        handle_learn,
    "estimate":     handle_estimate,
    "tool":         handle_tool,
    "idle-learn":   handle_idle_learn,
}
