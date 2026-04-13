"""
Reflection Engine — Analyzes project history to improve future performance.
Responsibility: Running post-mission analysis to capture and persist lessons learned.
"""
import os
import json
from synaptic.config import settings
from synaptic.core.agent_runner import AgentRunner
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.models.claude import ClaudeAdapter

class ReflectionEngine:
    """Analyzes recent project logs to update engineering standards."""

    def __init__(self):
        # Reflector uses the best available model for deep analysis
        if settings.CLAUDE_ACTIVE:
            model = ClaudeAdapter()
        elif settings.GEMINI_ACTIVE:
            model = GeminiAdapter()
        else:
            model = OllamaAdapter()
            
        self.reflector = AgentRunner(model, "reflector.md")
        self.lesson_dir = os.path.join(settings.SKILL_PATH, "autonomous-lessons")
        self.lesson_path = os.path.join(self.lesson_dir, "skill.md")

    def analyze(self, mission_id: str) -> str:
        """Reads logs for a mission, identifies key lessons, and updates the shared knowledge base."""
        os.makedirs(self.lesson_dir, exist_ok=True)
        log_file = os.path.join(settings.WORKSPACE_PATH, mission_id, "MISSION_LOG.md")
        
        if not os.path.exists(log_file):
            return f"Error: No logs found for project {mission_id}."

        with open(log_file, "r", encoding="utf-8") as f:
            audit_trail = f.read()

        print(f"[REVIEW] Reviewing project history: {mission_id}...")
        
        # Ask Reflector to synthesize lessons from the audit trail
        lessons = self.reflector.run(
            f"PROJECT_AUDIT_TRAIL:\n{audit_trail}",
            task="Analyzing Improvements",
            mission_id=mission_id
        )

        # Update the autonomous lessons skill
        header = "# Shared Engineering Lessons\n\n"
        timestamped_entry = f"## Progress Report: {mission_id}\n{lessons}\n\n---\n"
        
        mode = "a" if os.path.exists(self.lesson_path) else "w"
        with open(self.lesson_path, mode, encoding="utf-8") as f:
            if mode == "w": f.write(header)
            f.write(timestamped_entry)

        print(f"[LEARN] Review complete. Updated knowledge base: {self.lesson_path}")
        return lessons
