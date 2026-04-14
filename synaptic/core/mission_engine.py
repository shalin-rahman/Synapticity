"""
Mission Orchestrator - A simplified controller that sequences the development workflow.
It delegates state management, logging, and agent communication to specialized sub-components.
"""
import os
import time
import json
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.models.claude import ClaudeAdapter
from synaptic.core.agent_runner import AgentRunner
from synaptic.core.skill_registry import SkillRegistry
from synaptic.core.runtime_runner import RuntimeRunner
from synaptic.core.mission_state import MissionStateManager
from synaptic.core.mission_logger import MissionLogger
from synaptic.core.mission_workspace import MissionWorkspace
from synaptic.core.mission_gate import ApprovalGate
from synaptic.core.mission_phases import PlanningPhase, HealingCyclePhase
from synaptic.core.analytics import PerformanceAnalytics
from synaptic.core.agent_dispatcher import resolve_runner
from synaptic.utils.exceptions import ConfigurationError, WorkflowError
from synaptic.utils.logger import synaptic_log
from synaptic.utils.formatting import strip_markdown_backticks


class MissionEngine:
    """Manages the full development lifecycle by coordinating various specialized agents."""

    def __init__(self):
        # --- Model Routing ---
        self._analytics = PerformanceAnalytics()
        primary, fallback = self._resolve_optimal_routing()


        # --- Agents ---
        self.planner  = AgentRunner(primary, settings.AGENT_PM,       fallback_model=fallback)
        self.coder    = AgentRunner(primary, settings.AGENT_SWE,      fallback_model=fallback)
        self.tester   = AgentRunner(primary, settings.AGENT_QA,       fallback_model=fallback)
        self.auditor  = AgentRunner(primary, settings.AGENT_SECURITY, fallback_model=fallback)
        self.writer   = AgentRunner(primary, settings.AGENT_DOCS,     fallback_model=fallback)
        self.devops   = AgentRunner(primary, settings.AGENT_DEVOPS,   fallback_model=fallback)

        # Internal tools for project management
        self._skills   = SkillRegistry()
        self._runtime  = RuntimeRunner()
        self._log      = MissionLogger()
        self._gate     = ApprovalGate()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, mission_id: str, objective: str = None) -> None:
        """Starts or continues a development task."""
        start_time = time.time()
        path = os.path.join(settings.WORKSPACE_PATH, mission_id)
        os.makedirs(path, exist_ok=True)

        state_mgr = MissionStateManager(path)
        workspace = MissionWorkspace(path)
        state     = state_mgr.load()

        if objective:
            state["objective"] = objective

        synaptic_log.info(f"Starting work: {mission_id}")
        print(f"[START] Project {mission_id} (Phase: {state.get('phase', 'INITIAL')})")

        try:
            # Phase 1 — Planning
            if not state.get("specs"):
                planner = PlanningPhase(self.planner, self._skills, self._log)
                state["specs"] = planner.run(path, state, mission_id)
                state["phase"] = "PLANNED"
                state_mgr.save(state)
                self._log.persist(path, state)
                self._gate.request("Design specs are ready for review", state["phase"])

            # Phase 2 — Implementation
            if not state.get("code"):
                context       = self._skills.inject(state["objective"] + " " + state["specs"])
                raw_code      = self.coder.run(
                    state["specs"], context,
                    task="Synthesizing Source Code", mission_id=mission_id
                )
                state["code"] = strip_markdown_backticks(raw_code)
                self._log.log(state, "software-engineer", "Generated code based on specs.", state["code"])
                state["phase"] = "DEVELOPED"
                state_mgr.save(state)
                self._log.persist(path, state)
                self._gate.request("Initial code has been generated", state["phase"])

            # Phase 3 — Healing & Verification
            if state.get("phase") not in ("VERIFIED", "COMPLETED"):
                healer        = HealingCyclePhase(self.coder, self.tester, self.auditor, self._runtime, self._log)
                state["code"] = healer.run(path, state, state["specs"], state["code"], mission_id)
                state["phase"] = "VERIFIED"
                state_mgr.save(state)
                self._log.persist(path, state)

            if state.get("phase") != "COMPLETED":
                self._finalize(path, state, mission_id, workspace, state_mgr)

            self._log_mission_performance(mission_id, state, time.time() - start_time, success=True)

        except WorkflowError:
            self._log_mission_performance(mission_id, state, time.time() - start_time, success=False)
            raise
        except Exception as e:
            self._log_mission_performance(mission_id, state, time.time() - start_time, success=False)
            state["last_error"] = str(e)
            state_mgr.save(state)
            raise WorkflowError(
                f"Project '{mission_id}' stopped at '{state.get('phase', 'START')}': {e}"
            )

    def execute_single_agent(self, mission_id: str, agent_name: str, task: str) -> str:
        """Dispatches a solo agent to perform an isolated task on an existing mission."""
        path = os.path.join(settings.WORKSPACE_PATH, mission_id)
        if not os.path.exists(path):
            raise WorkflowError(f"Mission '{mission_id}' does not exist. Cannot dispatch agent.")

        state_mgr = MissionStateManager(path)
        state     = state_mgr.load()
        runner    = resolve_runner(self, agent_name)

        context   = state.get("specs", "") + "\n\n" + state.get("code", "")
        skills    = self._skills.inject(task + " " + context)

        print(f"[RUN] Sending {agent_name.upper()} into {mission_id}...")
        output = runner.run(
            f"DIRECTIVE:\n{task}\n\nCONTEXT:\n{context}\n\nSKILLS:\n{skills}",
            task=task, mission_id=mission_id
        )

        self._log.log(state, agent_name, f"SOLO DISPATCH: {task}", output)
        state_mgr.save(state)
        self._log.persist(path, state)

        from rich.console import Console
        Console().print(f"[OK] [bold green]{agent_name.upper()}[/] finished the task. Results are in the log.")
        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_optimal_routing(self) -> tuple:
        """Determines the best primary/fallback pair based on health and history."""
        gemini = GeminiAdapter() if settings.GEMINI_ACTIVE else None
        claude = ClaudeAdapter() if settings.CLAUDE_ACTIVE else None
        ollama = OllamaAdapter() if settings.OLLAMA_ACTIVE else None

        cloud = claude if settings.CLAUDE_ACTIVE else (gemini if settings.GEMINI_ACTIVE else None)

        # Basic hard-coded preference if everything is healthy
        p, f = None, None
        if settings.OLLAMA_ACTIVE:
            p, f = ollama, cloud
        elif cloud:
            p, f = cloud, (gemini if claude and settings.GEMINI_ACTIVE else None)
        else:
            raise ConfigurationError("No intelligence engines available.")

        # --- Autonomous Role Rotation Logic ---
        # Check if the primary model has a history of critical failure
        if os.path.exists(self._analytics.stats_file):
            try:
                with open(self._analytics.stats_file, "r") as r:
                    stats = json.load(r)
                
                model_key = type(p).__name__.replace("Adapter", "")
                if model_key == "Ollama": model_key = settings.OLLAMA_MODEL
                
                m_stats = stats.get("agent_metrics", {}).get(model_key)
                if m_stats and m_stats["total"] >= 3:
                    reliability = (1 - m_stats["failures"]/m_stats["total"]) * 100
                    if reliability < 40 and f:
                        print(f"[WARN] {model_key} reliability is low ({reliability}%). Rotating to fallback...")
                        p = f # Rotate primary to fallback
            except:
                pass

        return p, f

    def _log_mission_performance(self, mission_id: str, state: dict, duration: float, success: bool):
        """Standardized performance logging for mission analytics."""
        model_name = settings.OLLAMA_MODEL if settings.OLLAMA_ACTIVE else (
            settings.CLAUDE_MODEL if settings.CLAUDE_ACTIVE else settings.GEMINI_MODEL
        )
        self._analytics.log_mission_result(
            mission_id=mission_id,
            success=success,
            repairs=state.get("repair_count", 0),
            duration=duration,
            model=model_name
        )

    def _finalize(self, path, state, mission_id, workspace: MissionWorkspace, state_mgr: MissionStateManager) -> None:
        """Runs documentation, CI/CD synthesis, and workspace commit."""
        synaptic_log.info(f"MISSION FINALIZING: {mission_id}")

        print("[DOCS] Writing technical documentation...")
        docs = self.writer.run(
            f"Objective: {state['objective']}\nSpecs: {state['specs']}\nFinal Code: {state['code']}",
            task="Drafting Technical Hand-off", mission_id=mission_id
        )
        self._log.log(state, "writer", "Generated technical hand-off documentation.", docs)

        print("[CI] Generating the CI/CD pipeline...")
        pipeline = self.devops.run(
            f"Objective: {state['objective']}\nRepository Tech Stack Code:\n{state['code']}",
            task="Architecting GitHub Actions Pipeline", mission_id=mission_id
        )
        self._log.log(state, "devops-engineer", "Generated GitHub Actions YAML.", pipeline)

        workspace.commit_code(state["code"])
        workspace.commit_docs(docs)
        workspace.commit_pipeline(pipeline)

        state["phase"] = "COMPLETED"
        state_mgr.save(state)
        self._log.persist(path, state)
        print(f"[DONE] Finished: {mission_id}")
