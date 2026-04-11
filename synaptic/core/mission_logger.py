"""
Mission audit logger — history appending and MISSION_LOG.md generation.
Single Responsibility: owns all human-readable audit trail output.
"""
import os
import time


class MissionLogger:
    """Appends history entries and persists MISSION_LOG.md."""

    def log(self, state: dict, role: str, thought: str, content: str) -> None:
        """Appends a timestamped event to the in-memory state history."""
        if "history" not in state:
            state["history"] = []
        state["history"].append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role":      role,
            "thought":   thought,
            "content":   content,
        })

    def persist(self, mission_path: str, state: dict) -> None:
        """Writes the full in-memory history out to MISSION_LOG.md."""
        log_path = os.path.join(mission_path, "MISSION_LOG.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# Synaptic Mission Log: {state.get('title', 'Unknown')}\n\n")
            f.write(f"- **Objective:** {state.get('objective')}\n")
            f.write(f"- **Status:** {state.get('phase')}\n")
            f.write(f"- **Final Verdict:** {state.get('verdict', 'Pending')}\n\n")
            f.write("## [LOG] Intellectual Audit Trail\n\n")

            for entry in state.get("history", []):
                f.write(f"### [TIME] {entry['timestamp']} | Role: {entry['role'].upper()}\n")
                f.write(f"**Action:** {entry.get('thought', 'Processing Task')}\n\n")
                content = entry["content"]
                f.write("```text\n")
                f.write(content[:1000] + "\n... [TRUNCATED for brevity] ..." if len(content) > 1000 else content)
                f.write("\n```\n\n")
