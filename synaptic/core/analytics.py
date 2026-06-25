import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List
from synaptic.config import settings
from synaptic.utils.logger import synaptic_log


class PerformanceAnalytics:
    """
    Tracks and analyzes Agent Performance Scorecards (First-Pass Success vs. Repair Required).
    Maintains persistent logs of execution metrics for the framework.
    """

    def __init__(self):
        self.stats_file = os.path.join(settings.WORKSPACE_PATH, "performance_metrics.json")
        self._ensure_stats_file()

    def _ensure_stats_file(self):
        """Initializes the metrics file if it doesn't exist."""
        if not os.path.exists(self.stats_file):
            initial_data = {
                "total_missions": 0,
                "first_pass_success_rate": 0.0,
                "average_repairs_per_mission": 0.0,
                "agent_metrics": {},
                "inference_metrics": {},
                "mission_history": [],
            }
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4)

    # ------------------------------------------------------------------
    # Async public API — offloads blocking file I/O to a thread pool
    # ------------------------------------------------------------------

    async def log_mission_result(self, mission_id: str, success: bool, repairs: int, duration: float, model: str):
        """Records the outcome of a completed mission (non-blocking)."""
        await asyncio.to_thread(self._sync_log_mission_result, mission_id, success, repairs, duration, model)

    async def log_inference(self, model: str, duration: float):
        """Records the duration of a single inference request (non-blocking)."""
        await asyncio.to_thread(self._sync_log_inference, model, duration)

    # ------------------------------------------------------------------
    # Synchronous I/O implementations (run inside thread pool)
    # ------------------------------------------------------------------

    def _sync_log_mission_result(self, mission_id: str, success: bool, repairs: int, duration: float, model: str):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["total_missions"] += 1

            successful_missions = len([m for m in data["mission_history"] if m["success"]]) + (1 if success else 0)
            data["first_pass_success_rate"] = round(
                (successful_missions / data["total_missions"]) * 100, 2
            )

            entry = {
                "timestamp": datetime.now().isoformat(),
                "mission_id": mission_id,
                "success": success,
                "repairs": repairs,
                "duration_seconds": round(duration, 2),
                "model_used": model,
            }
            data["mission_history"].append(entry)

            if model not in data["agent_metrics"]:
                data["agent_metrics"][model] = {"total": 0, "repairs": 0, "failures": 0}

            data["agent_metrics"][model]["total"] += 1
            data["agent_metrics"][model]["repairs"] += repairs
            if not success:
                data["agent_metrics"][model]["failures"] += 1

            if len(data["mission_history"]) > 100:
                data["mission_history"] = data["mission_history"][-100:]

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            synaptic_log.info(
                f"[ANALYTICS] Performance logged for {mission_id}: Success={success}, Repairs={repairs}"
            )
        except Exception as e:
            synaptic_log.error(f"[ANALYTICS] Failed to log mission metrics: {e}")

    def _sync_log_inference(self, model: str, duration: float):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "inference_metrics" not in data:
                data["inference_metrics"] = {}

            if model not in data["inference_metrics"]:
                data["inference_metrics"][model] = {"calls": 0, "total_duration": 0.0}

            data["inference_metrics"][model]["calls"] += 1
            data["inference_metrics"][model]["total_duration"] += duration

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            synaptic_log.debug(f"[ANALYTICS] Could not log inference duration: {e}")

    # ------------------------------------------------------------------
    # Sync report — called from the CLI stats handler (no event loop)
    # ------------------------------------------------------------------

    def get_summary_report(self) -> str:
        """Returns a formatted summary of the performance metrics."""
        if not os.path.exists(self.stats_file):
            return "No performance data available."

        with open(self.stats_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = "\n[📊] SYSTEM PERFORMANCE REPORT\n"
        report += "----------------------------------\n"
        report += f"Total Projects Done: {data['total_missions']}\n"
        report += f"Success Rate: {data['first_pass_success_rate']}%\n"
        report += "Model Performance:\n"

        for model, metrics in data["agent_metrics"].items():
            latency_info = ""
            inf_metrics = data.get("inference_metrics", {}).get(model)
            if inf_metrics:
                avg_lat = round(inf_metrics["total_duration"] / inf_metrics["calls"], 2)
                latency_info = f" | Avg Speed: {avg_lat}s"

            reliability = round((1 - metrics["failures"] / metrics["total"]) * 100, 1)
            report += f"  - {model} | Reliability: {reliability}%{latency_info}\n"

        return report
