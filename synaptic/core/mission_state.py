"""
Mission state persistence — CRUD over state.json.
Single Responsibility: owns all disk I/O for mission state.
"""
import os
import json
from synaptic.config import settings
from synaptic.utils.logger import synaptic_log


class MissionStateManager:
    """Reads and writes mission state.json files."""

    def __init__(self, mission_path: str):
        self._path = os.path.join(mission_path, settings.STATE_FILE)

    def load(self) -> dict:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                synaptic_log.error(f"State file corrupted: {self._path}: {e}. Re-initializing.")
                print("[WARN] Synaptic Recovery: Mission state corrupted. Re-initializing...")
        return {"phase": "START", "objective": ""}

    def save(self, state: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
