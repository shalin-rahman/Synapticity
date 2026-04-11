"""
Agent dispatcher — resolves agent aliases and executes solo dispatches.
Single Responsibility: owns all agent name-to-runner resolution logic.
"""
from synaptic.utils.exceptions import WorkflowError


# Maps keyword tokens -> runner attribute name on MissionEngine
_AGENT_MAP = {
    ("pm", "product"):               "planner",
    ("swe", "coder", "software"):    "coder",
    ("test", "qa"):                  "tester",
    ("oncall", "security", "audit"): "auditor",
    ("writer", "doc"):               "writer",
    ("devops", "deploy", "ci"):      "devops",
}


def resolve_runner(engine, agent_name: str):
    """Returns the AgentRunner matching a fuzzy agent alias."""
    normalized = agent_name.lower().strip()
    for tokens, attr in _AGENT_MAP.items():
        if any(t in normalized for t in tokens):
            return getattr(engine, attr)
    raise WorkflowError(
        f"Unknown agent: '{agent_name}'. Valid agents: pm, swe, tester, oncall, writer, devops."
    )
