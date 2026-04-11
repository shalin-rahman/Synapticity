"""
Mission Engine — thin orchestrator coordinating all mission sub-systems.
Responsibility: phase sequencing only. All logic delegated to sub-components.
"""
import os
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.core.agent_runner import AgentRunner
from synaptic.core.skill_registry import SkillRegistry
from synaptic.core.runtime_runner import RuntimeRunner
from synaptic.core.mission_state import MissionStateManager
from synaptic.core.mission_logger import MissionLogger
from synaptic.core.mission_workspace import MissionWorkspace
from synaptic.core.mission_gate import ApprovalGate
from synaptic.core.mission_phases import PlanningPhase, HealingCyclePhase
from synaptic.core.agent_dispatcher import resolve_runner
from synaptic.utils.exceptions import ConfigurationError, WorkflowError
from synaptic.utils.logger import synaptic_log
from synaptic.utils.formatting import strip_markdown_backticks


class MissionEngine:
    """Coordinates the full SDLC lifecycle by delegating to focused sub-systems."""

    def __init__(self):
        # --- Model Routing ---
        cloud = GeminiAdapter() if settings.GEMINI_ACTIVE else None
        local = OllamaAdapter() if settings.OLLAMA_ACTIVE else None

        if settings.OLLAMA_ACTIVE:
            primary, fallback = local, cloud
        elif settings.GEMINI_ACTIVE:
            primary, fallback = cloud, None
        else:
            raise ConfigurationError(
                "CRITICAL: Both Ollama and Gemini are INACTIVE. No intelligence engine available."
            )

        # --- Agents ---
        self.planner  = AgentRunner(primary, settings.AGENT_PM,       fallback_model=fallback)
        self.coder    = AgentRunner(primary, settings.AGENT_SWE,      fallback_model=fallback)
        self.tester   = AgentRunner(primary, settings.AGENT_QA,       fallback_model=fallback)
        self.auditor  = AgentRunner(primary, settings.AGENT_SECURITY, fallback_model=fallback)
        self.writer   = AgentRunner(primary, settings.AGENT_DOCS,     fallback_model=fallback)
        self.devops   = AgentRunner(primary, settings.AGENT_DEVOPS,   fallback_model=fallback)

        # --- Sub-Systems ---
        self._skills   = SkillRegistry()
        self._runtime  = RuntimeRunner()
        self._log      = MissionLogger()
        self._gate     = ApprovalGate()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_mission(self, mission_id: str, objective: str = None) -> None:
        """Starts or resumes a mission, coordinating all four SDLC phases."""
        path = os.path.join(settings.WORKSPACE_PATH, mission_id)
        os.makedirs(path, exist_ok=True)

        state_mgr = MissionStateManager(path)
        workspace = MissionWorkspace(path)
        state     = state_mgr.load()

        if objective:
            state["objective"] = objective

        synaptic_log.info(f"MISSION START: {mission_id} | Objective: {state['objective']}")
        print(f"[LAUNCH] synaptic Engaged | Mission: {mission_id} (Phase: {state.get('phase', 'INITIAL')})")

        try:
            # Phase 1 — Planning
            if not state.get("specs"):
                planner = PlanningPhase(self.planner, self._skills, self._log)
                state["specs"] = planner.run(path, state, mission_id)
                state["phase"] = "PLANNED"
                state_mgr.save(state)
                self._log.persist(path, state)
                self._gate.request("Mission Architecture Ready", state["phase"])

            # Phase 2 — Implementation
            if not state.get("code"):
                context       = self._skills.inject(state["objective"] + " " + state["specs"])
                raw_code      = self.coder.execute(
                    state["specs"], context,
                    task="Synthesizing Source Code", mission_id=mission_id
                )
                state["code"] = strip_markdown_backticks(raw_code)
                self._log.log(state, "software-engineer", "Synthesized implementation from specs.", state["code"])
                state["phase"] = "DEVELOPED"
                state_mgr.save(state)
                self._log.persist(path, state)
                self._gate.request("Code Generated", state["phase"])

            # Phase 3 — Healing & Verification
            if state.get("phase") not in ("VERIFIED", "COMPLETED"):
                healer        = HealingCyclePhase(self.coder, self.tester, self.auditor, self._runtime, self._log)
                state["code"] = healer.run(path, state, state["specs"], state["code"], mission_id)
                state["phase"] = "VERIFIED"
                state_mgr.save(state)
                self._log.persist(path, state)

            # Phase 4 — Documentation & CI/CD
            if state.get("phase") != "COMPLETED":
                self._finalize(path, state, mission_id, workspace, state_mgr)

        except WorkflowError:
            raise
        except Exception as e:
            state["last_error"] = str(e)
            state_mgr.save(state)
            raise WorkflowError(
                f"Mission '{mission_id}' failed during Phase '{state.get('phase', 'START')}': {e}"
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

        print(f"[LAUNCH] Dispatching solo agent: {agent_name.upper()} on Mission: {mission_id}")
        output = runner.execute(
            f"SOLO DIRECTIVE:\n{task}\n\nWORKSPACE CONTEXT:\n{context}\n\nSKILLS:\n{skills}",
            task=task, mission_id=mission_id
        )

        self._log.log(state, agent_name, f"SOLO DISPATCH: {task}", output)
        state_mgr.save(state)
        self._log.persist(path, state)

        from rich.console import Console
        Console().print(f"[OK] [bold green]{agent_name.upper()}[/] completed task. Output appended to MISSION_LOG.md.")
        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _finalize(self, path, state, mission_id, workspace: MissionWorkspace, state_mgr: MissionStateManager) -> None:
        """Runs documentation, CI/CD synthesis, and workspace commit."""
        synaptic_log.info(f"MISSION FINALIZING: {mission_id}")

        print("[DOCS] Finalizing technical documentation...")
        docs = self.writer.execute(
            f"Objective: {state['objective']}\nSpecs: {state['specs']}\nFinal Code: {state['code']}",
            task="Drafting Technical Hand-off", mission_id=mission_id
        )
        self._log.log(state, "writer", "Generated technical hand-off documentation.", docs)

        print("[DEVOPS] Synthesizing CI/CD pipeline...")
        pipeline = self.devops.execute(
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
        print(f"[DONE] Mission Accomplished: {mission_id}")
