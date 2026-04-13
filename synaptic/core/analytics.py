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
                "mission_history": []
            }
            with open(self.stats_file, "w") as f:
                json.dump(initial_data, f, indent=4)

    def log_mission_result(self, mission_id: str, success: bool, repairs: int, duration: float, model: str):
        """Records the outcome of a completed mission."""
        try:
            with open(self.stats_file, "r") as f:
                data = json.load(f)

            # Update global counts
            data["total_missions"] += 1
            
            # Calculate success rate
            successful_missions = len([m for m in data["mission_history"] if m["success"]]) + (1 if success else 0)
            data["first_pass_success_rate"] = round((successful_missions / data["total_missions"]) * 100, 2)

            # Record entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "mission_id": mission_id,
                "success": success,
                "repairs": repairs,
                "duration_seconds": round(duration, 2),
                "model_used": model
            }
            data["mission_history"].append(entry)

            # Update Model-Specific Stats
            if model not in data["agent_metrics"]:
                data["agent_metrics"][model] = {"total": 0, "repairs": 0, "failures": 0}
            
            data["agent_metrics"][model]["total"] += 1
            data["agent_metrics"][model]["repairs"] += repairs
            if not success:
                data["agent_metrics"][model]["failures"] += 1

            # Keep history manageable
            if len(data["mission_history"]) > 100:
                data["mission_history"] = data["mission_history"][-100:]

            with open(self.stats_file, "w") as f:
                json.dump(data, f, indent=4)

            synaptic_log.info(f"[ANALYTICS] Performance logged for {mission_id}: Success={success}, Repairs={repairs}")

        except Exception as e:
            synaptic_log.error(f"[ANALYTICS] Failed to log mission metrics: {e}")

    def log_inference(self, model: str, duration: float):
        """Records the duration of a single inference request."""
        try:
            with open(self.stats_file, "r") as f:
                data = json.load(f)

            if "inference_metrics" not in data:
                data["inference_metrics"] = {}

            if model not in data["inference_metrics"]:
                data["inference_metrics"][model] = {"calls": 0, "total_duration": 0.0}

            data["inference_metrics"][model]["calls"] += 1
            data["inference_metrics"][model]["total_duration"] += duration

            with open(self.stats_file, "w") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            synaptic_log.debug(f"[ANALYTICS] Could not log inference duration: {e}")

    def get_summary_report(self) -> str:
        """Returns a formatted summary of the performance metrics."""
        if not os.path.exists(self.stats_file):
            return "No performance data available."

        with open(self.stats_file, "r") as f:
            data = json.load(f)

        report = f"\n[📊] FRAMEWORK PERFORMANCE REPORT\n"
        report += f"----------------------------------\n"
        report += f"Total Missions Conducted: {data['total_missions']}\n"
        report += f"First-Pass Success Rate: {data['first_pass_success_rate']}%\n"
        report += f"Active Insights:\n"
        
        for model, metrics in data["agent_metrics"].items():
            avg_repair = round(metrics['repairs'] / metrics['total'], 2) if metrics['total'] > 0 else 0
            
            latency_info = ""
            inf_metrics = data.get("inference_metrics", {}).get(model)
            if inf_metrics:
                avg_lat = round(inf_metrics["total_duration"] / inf_metrics["calls"], 2)
                latency_info = f" | Avg Latency: {avg_lat}s"
                
            report += f"  - Model: {model} | Reliability: {round((1 - metrics['failures']/metrics['total'])*100, 1)}%{latency_info}\n"
            
        return report
