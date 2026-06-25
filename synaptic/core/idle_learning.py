"""
Idle Learning Mode — auto-retry failed missions when the machine is idle.

Components:
  IdleDetector          — CPU load + time-since-last-user-input (Windows native)
  FailedMissionScanner  — finds failed/stalled missions in workspace/
  IdleLearningScheduler — async loop: detect idle -> scan -> replay -> reflect
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from synaptic.config import settings
from synaptic.utils.logger import synaptic_log


# ─────────────────────────────────────────────────────────────
# Idle detection
# ─────────────────────────────────────────────────────────────

class IdleDetector:
    """Reports machine idleness from CPU load and user-input inactivity."""

    @staticmethod
    def cpu_percent() -> float:
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0

    @staticmethod
    def secs_since_last_input() -> float:
        """Seconds since last keyboard/mouse input (Windows only; returns 0 elsewhere)."""
        try:
            import ctypes
            import ctypes.wintypes

            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            elapsed_ms = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(elapsed_ms / 1000.0, 0.0)
        except Exception:
            return 0.0

    @classmethod
    def is_idle(cls) -> bool:
        cpu = cls.cpu_percent()
        idle_input = cls.secs_since_last_input()
        return cpu < settings.IDLE_CPU_THRESHOLD and idle_input >= settings.IDLE_INPUT_TIMEOUT


# ─────────────────────────────────────────────────────────────
# Failed mission scanner
# ─────────────────────────────────────────────────────────────

_INCOMPLETE_PHASES = {"PLANNED", "DEVELOPED", "VERIFIED"}
_PHASE_RANK = {"PLANNED": 1, "DEVELOPED": 2, "VERIFIED": 3}


class FailedMissionScanner:
    """Scans workspace/ for missions that failed or stalled before completion."""

    def __init__(self, log_path: str):
        self._log_path = log_path
        self._log = self._load_log()

    def _load_log(self) -> dict:
        if os.path.exists(self._log_path):
            try:
                with open(self._log_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"replays": {}}

    def _save_log(self) -> None:
        os.makedirs(os.path.dirname(self._log_path) or ".", exist_ok=True)
        with open(self._log_path, "w", encoding="utf-8") as f:
            json.dump(self._log, f, indent=2, ensure_ascii=False)

    def scan(self) -> List[Dict]:
        """Return eligible failed missions sorted by (attempts asc, phase_rank desc)."""
        workspace = settings.WORKSPACE_PATH
        if not os.path.isdir(workspace):
            return []

        candidates = []
        for name in os.listdir(workspace):
            mission_path = os.path.join(workspace, name)
            if not os.path.isdir(mission_path):
                continue
            state_file = os.path.join(mission_path, settings.STATE_FILE)
            if not os.path.exists(state_file):
                continue

            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                continue

            phase = state.get("phase", "START")
            if phase not in _INCOMPLETE_PHASES:
                continue

            replay_info = self._log["replays"].get(name, {})
            attempts = replay_info.get("attempts", 0)
            if attempts >= settings.IDLE_MAX_RETRIES:
                continue

            candidates.append({
                "mission_id": name,
                "path": mission_path,
                "phase": phase,
                "phase_rank": _PHASE_RANK.get(phase, 0),
                "has_error": bool(state.get("last_error")),
                "objective": state.get("objective", "(no objective)"),
                "attempts": attempts,
                "last_outcome": replay_info.get("last_outcome", "pending"),
            })

        candidates.sort(key=lambda m: (m["attempts"], -m["phase_rank"]))
        return candidates

    def mark_attempt(self, mission_id: str) -> None:
        entry = self._log["replays"].setdefault(mission_id, {"attempts": 0, "history": []})
        entry["attempts"] = entry.get("attempts", 0) + 1
        entry["last_attempted"] = datetime.now(timezone.utc).isoformat()
        self._save_log()

    def mark_result(self, mission_id: str, outcome: str) -> None:
        entry = self._log["replays"].setdefault(mission_id, {"attempts": 0, "history": []})
        entry["last_outcome"] = outcome
        entry.setdefault("history", []).append({
            "at": datetime.now(timezone.utc).isoformat(),
            "outcome": outcome,
        })
        self._save_log()

    def get_log(self) -> dict:
        return self._log


# ─────────────────────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────────────────────

class IdleLearningScheduler:
    """
    Main idle-learning loop.
    When the machine is idle, picks the highest-priority failed mission,
    re-runs it through MissionEngine, then reflects via ReflectionEngine.
    """

    REPLAY_LOG = os.path.join(settings.WORKSPACE_PATH, ".idle_learning_log.json")

    def __init__(self):
        self._scanner = FailedMissionScanner(self.REPLAY_LOG)

    # ── public API ────────────────────────────────────────────

    async def run(self, once: bool = False, dry_run: bool = False) -> None:
        """
        Monitoring loop.
        once=True  → one idle check then exit
        dry_run    → preview only, no missions executed
        """
        synaptic_log.info("[IDLE-LEARN] Scheduler started")
        print(
            f"[IDLE-LEARN] Monitoring for idle machine "
            f"(CPU < {settings.IDLE_CPU_THRESHOLD}%, "
            f"input idle > {settings.IDLE_INPUT_TIMEOUT}s). "
            f"Interval: {settings.IDLE_CHECK_INTERVAL}s"
        )
        if not dry_run:
            print("[IDLE-LEARN] Press Ctrl+C to stop.\n")

        while True:
            cpu = IdleDetector.cpu_percent()
            inp = IdleDetector.secs_since_last_input()
            idle = cpu < settings.IDLE_CPU_THRESHOLD and inp >= settings.IDLE_INPUT_TIMEOUT

            if idle:
                print(f"[IDLE-LEARN] Idle (CPU={cpu:.1f}%, input={inp:.0f}s). Scanning...")
                await self._run_one_replay(dry_run)
            else:
                print(f"[IDLE-LEARN] Busy (CPU={cpu:.1f}%, input={inp:.0f}s). Waiting...")

            if once:
                break
            await asyncio.sleep(settings.IDLE_CHECK_INTERVAL)

    async def run_now(self, dry_run: bool = False) -> Optional[str]:
        """Force one replay cycle immediately, regardless of idle state."""
        return await self._run_one_replay(dry_run, force=True)

    def status(self) -> dict:
        return {
            "replay_log": self._scanner.get_log(),
            "pending": self._scanner.scan(),
        }

    # ── private ──────────────────────────────────────────────

    async def _run_one_replay(self, dry_run: bool, force: bool = False) -> Optional[str]:
        candidates = self._scanner.scan()
        if not candidates:
            print("[IDLE-LEARN] No eligible failed missions found.")
            return None

        mission = candidates[0]
        mission_id = mission["mission_id"]
        print(
            f"[IDLE-LEARN] Replaying: {mission_id} | "
            f"phase={mission['phase']} | "
            f"attempts={mission['attempts']} | "
            f"objective: {mission['objective'][:60]}"
        )

        if dry_run:
            print("[IDLE-LEARN] --dry-run active: no execution.")
            return mission_id

        self._scanner.mark_attempt(mission_id)
        success = await self._replay(mission_id)
        outcome = "success" if success else "failed"
        self._scanner.mark_result(mission_id, outcome)
        print(f"[IDLE-LEARN] Replay {outcome}: {mission_id}")

        if success:
            await self._reflect(mission_id)

        return mission_id

    async def _replay(self, mission_id: str) -> bool:
        from synaptic.core.mission_engine import MissionEngine
        try:
            engine = MissionEngine()
            await engine.run(mission_id)
            synaptic_log.info(f"[IDLE-LEARN] Replay success: {mission_id}")
            return True
        except Exception as e:
            synaptic_log.warning(f"[IDLE-LEARN] Replay failed for {mission_id}: {e}")
            return False

    async def _reflect(self, mission_id: str) -> None:
        from synaptic.core.self_learning import ReflectionEngine
        try:
            engine = ReflectionEngine()
            await engine.analyze(mission_id)
            print(f"[IDLE-LEARN] Reflection complete: {mission_id}")
        except Exception as e:
            synaptic_log.warning(f"[IDLE-LEARN] Reflection failed for {mission_id}: {e}")
