import os
import json
import time
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.core.orchestrator import AgentRunner
from synaptic.core.skills import SkillRegistry
from synaptic.core.runtime import RuntimeRunner
from synaptic.utils.hashing import generate_context_hash
from synaptic.utils.exceptions import WorkflowError
from synaptic.utils.logger import synaptic_log

class MissionEngine:
    """Manages the full SDLC mission lifecycle with Checkpointing and HITL Gating."""
    
    def __init__(self):
        # Resource Adapters
        self.cloud = GeminiAdapter()
        self.local = OllamaAdapter()
        self.skills = SkillRegistry()
        
        # Specialized Runners
        self.planner = AgentRunner(self.cloud, settings.AGENT_PM)
        self.coder = AgentRunner(self.local, settings.AGENT_SWE)
        self.tester = AgentRunner(self.local, settings.AGENT_QA)
        self.auditor = AgentRunner(self.cloud, settings.AGENT_SECURITY)
        self.writer = AgentRunner(self.cloud, settings.AGENT_DOCS)
        self.runtime = RuntimeRunner()
        
        self.state = {}

    def execute_mission(self, mission_id: str, objective: str = None):
        """Starts or resumes a specialized software development mission."""
        path = os.path.join(settings.WORKSPACE_PATH, mission_id)
        os.makedirs(path, exist_ok=True)
        
        try:
            # Load state if resuming
            self.state = self._load_state(path)
            if objective:
                self.state["objective"] = objective
            
            synaptic_log.info(f"MISSION START: {mission_id} | Objective: {self.state['objective']}")
            print(f"🚀 synaptic Engaged | Mission: {mission_id} (Phase: {self.state.get('phase', 'INITIAL')})")

            # Milestone 1: Planning
            if not self.state.get("specs"):
                self.state["specs"] = self._solve_planning(path, self.state["objective"])
                self.state["phase"] = "PLANNED"
                self._save_state(path)
                self._request_approval("Mission Architecture Ready")

            # Milestone 2: Implementation
            if not self.state.get("code"):
                context = self.skills.inject(self.state["objective"] + " " + self.state["specs"])
                self.state["code"] = self.coder.execute(self.state["specs"], context)
                self._log_history("software-engineer", self.state["code"])
                self.state["phase"] = "DEVELOPED"
                self._save_state(path)
                self._request_approval("Code Generated")

            # Milestone 3: Verification & Healing
            if self.state.get("phase") != "VERIFIED":
                self.state["code"] = self._run_healing_cycle(self.state["specs"], self.state["code"])
                self.state["phase"] = "VERIFIED"
                self._save_state(path)

            # Milestone 4: Deployment & Documentation
            if self.state.get("phase") != "COMPLETED":
                synaptic_log.info(f"MISSION FINALIZING: {mission_id}")
                print("📝 Finalizing technical documentation...")
                docs = self.writer.execute(f"Objective: {self.state['objective']}\nSpecs: {self.state['specs']}\nFinal Code: {self.state['code']}")
                
                self._commit_to_workspace(path, self.state["code"], docs)
                self.state["phase"] = "COMPLETED"
                self._save_state(path)
                print(f"🏁 Mission Accomplished: {mission_id}")
                
        except Exception as e:
            self.state["last_error"] = str(e)
            self._save_state(path)
            raise WorkflowError(f"Mission {mission_id} failed during Phase {self.state.get('phase', 'START')}: {e}")

    def _solve_planning(self, path, objective) -> str:
        ctx_hash = generate_context_hash(path)
        cache_file = os.path.join(path, "specs.json")
        
        if ctx_hash and os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
                if data.get("hash") == ctx_hash:
                    print("♻️  Specs retrieved from synaptic Cache.")
                    return data["specs"]

        print("🧠 Planning mission architecture...")
        specs = self.planner.execute(objective)
        
        if ctx_hash:
            with open(cache_file, "w") as f:
                json.dump({"hash": ctx_hash, "specs": specs}, f)
        return specs

    def _run_healing_cycle(self, specs, initial_code) -> str:
        code = initial_code
        for i in range(1, settings.MAX_RETRY_ATTEMPTS + 1):
            print(f"🛡️  Verification Loop {i}...")
            
            # --- REAL RUNTIME EXECUTION ---
            print("🧪 Running code in sandbox...")
            execution = self.runtime.run_python_code(code)
            
            runtime_log = f"SUCCESS: {execution['success']}\nSTDOUT: {execution['stdout']}\nSTDERR: {execution['stderr']}"
            
            # QA Pass (informed by real runtime logs)
            qa_res = self.tester.execute(f"Specs: {specs}\nRuntime Logs: {runtime_log}\nCode: {code}")
            
            # Security Pass (Informed by Bandit Static Analysis)
            print("🛡️  Running security scan...")
            static_audit = self.runtime.scan_security(code)
            
            sec_res = self.auditor.execute(f"CODE:\n{code}\nSTATIC_SCAN_REPORT: {static_audit['summary']}")
            
            if "VERDICT: SECURE" in sec_res and "VERDICT: PASS" in qa_res:
                print("✅ Code validated and secured.")
                return code
                
            print("🛠️  Initiating synaptic Auto-Remediation...")
            directive = sec_res if "VERDICT: NEEDS_FIX" in sec_res else qa_res
            code = self.coder.execute(f"REMEDIATION: {directive}\nORIGINAL: {code}")
            
        print("🛑 Critical Failure: synaptic could not stabilize the output.")
        return code

    def _request_approval(self, message):
        """Prompts for user approval if INTERACTIVE_MODE is active."""
        if settings.INTERACTIVE_MODE:
            print(f"\n[INTERACTIVE GATING] {message}")
            choice = input("Press ENTER to proceed, or 'q' to abort mission: ").lower()
            if choice == 'q':
                print("🛑 Mission manually aborted by operator.")
                exit(0)

    def _log_history(self, role, content):
        """Appends an event to the mission's audit log."""
        if "history" not in self.state:
            self.state["history"] = []
        
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "content": content[:500] + "..." if len(content) > 500 else content
        }
        self.state["history"].append(entry)

    def _save_state(self, path):
        state_path = os.path.join(path, settings.STATE_FILE)
        with open(state_path, "w") as f:
            json.dump(self.state, f)

    def _load_state(self, path):
        state_path = os.path.join(path, settings.STATE_FILE)
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                return json.load(f)
        return {"phase": "START", "objective": ""}

    def _commit_to_workspace(self, path, code, docs=""):
        out = os.path.join(path, "output")
        os.makedirs(out, exist_ok=True)
        
        # Save Code
        with open(os.path.join(out, "main.py"), "w") as f:
            f.write(code)
            
        # Save Documentation
        if docs:
            with open(os.path.join(out, "TECHNICAL_DOCS.md"), "w") as f:
                f.write(docs)
