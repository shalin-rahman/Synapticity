"""
Mission phase executors — planning and healing cycle.
Single Responsibility: owns the intelligence logic for each SDLC phase.
"""
import os
import json
import re
import concurrent.futures
from rich.panel import Panel
from rich.console import Console
from synaptic.config import settings
from synaptic.utils.hashing import generate_context_hash
from synaptic.utils.formatting import strip_markdown_backticks

_console = Console()


class PlanningPhase:
    """Executes the architectural specification phase."""

    def __init__(self, planner, skill_registry, logger):
        self._planner  = planner
        self._skills   = skill_registry
        self._logger   = logger

    def run(self, mission_path: str, state: dict, mission_id: str) -> str:
        """Returns the produced architectural specs string."""
        ctx_hash   = generate_context_hash(mission_path)
        cache_file = os.path.join(mission_path, "specs.json")

        # Cache hit — skip LLM call
        if ctx_hash and os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("hash") == ctx_hash:
                print("[CACHE] Specs retrieved from synaptic Cache.")
                return data["specs"]

        print("[AI] Planning mission architecture...")
        specs = self._planner.execute(state["objective"], task="Drafting Architectural Specs", mission_id=mission_id)

        # Extract title from leading H1 heading if present
        title_match = re.search(r"^# (.*)", specs)
        state["title"] = title_match.group(1).strip() if title_match else state["objective"][:30] + "..."
        self._logger.log(state, "product-manager", f"Established Mission Objective: {state['title']}", specs)

        if ctx_hash:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"hash": ctx_hash, "specs": specs}, f)

        return specs


class HealingCyclePhase:
    """Executes the iterative verification and auto-remediation loop."""

    def __init__(self, coder, tester, auditor, runtime, logger):
        self._coder   = coder
        self._tester  = tester
        self._auditor = auditor
        self._runtime = runtime
        self._logger  = logger

    def run(self, mission_path: str, state: dict, specs: str, code: str, mission_id: str) -> str:
        """Returns the verified (or best-effort) code after up to MAX_RETRY_ATTEMPTS passes."""
        for i in range(1, settings.MAX_RETRY_ATTEMPTS + 1):
            print(f"[SEC] Parallel Verification Loop {i}...")

            execution    = self._run_sandbox(code)
            runtime_log  = f"SUCCESS: {execution['success']}\nSTDOUT: {execution['stdout']}\nSTDERR: {execution['stderr']}"
            quality      = self._runtime.scan_quality(code)

            # Dispatch QA and Security in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                qa_future  = executor.submit(self._run_qa, specs, runtime_log, quality, code, mission_id, i, state)
                sec_future = executor.submit(self._run_security, code, mission_id, i, state)
                
                qa_result  = qa_future.result()
                sec_result = sec_future.result()

            if "VERDICT: SECURE" in sec_result and "VERDICT: PASS" in qa_result and quality["clean"]:
                print("[OK] Code validated, secured, and lint-free.")
                state["verdict"] = "[bold green][OK] PASSED[/]"
                return code

            state["verdict"] = "[bold red][FAIL] FAILED[/]"
            print("[REPAIR] Initiating synaptic Auto-Remediation...")
            directive = (
                f"IDE_PROBLEMS:\n{quality['problems']}\n\nQA_DIRECTIVE:\n{qa_result}"
                if not quality["clean"] or "VERDICT: NEEDS_FIX" in qa_result
                else sec_result
            )
            raw_repair = self._coder.execute(
                f"REMEDIATION_DIRECTIVE: {directive}\nORIGINAL_CODE: {code}",
                task="Applying Expert Remediation",
                mission_id=mission_id
            )
            code = strip_markdown_backticks(raw_repair)
            self._logger.log(state, "software-engineer", "Applied auto-remediation patch.", code)

        print("[HALT] Critical Failure: synaptic could not stabilize the output.")
        return code

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_sandbox(self, code: str) -> dict:
        print("[TEST] Running code in sandbox...")
        result    = self._runtime.run_python_code(code)
        res_color = "green" if result["success"] else "red"
        _console.print(Panel(
            f"[bold]Status:[/] [{res_color}]{'SUCCESS' if result['success'] else 'FAILED'}[/]\n"
            f"[bold]Duration:[/] {result['duration']}s\n\n"
            f"[dim]STDOUT:[/]\n{result['stdout'] or '(empty)'}\n\n"
            f"[dim]STDERR:[/]\n[red]{result['stderr'] or '(none)'}[/]",
            title="[TEST] Sandbox Execution Logs",
            border_style=res_color,
            expand=False
        ))
        return result

    def _run_qa(self, specs, runtime_log, quality, code, mission_id, loop_i, state) -> str:
        print("[SCAN] Scanning for structural 'Problems' (IDE Simulation)...")
        result = self._tester.execute(
            f"Specs: {specs}\nRuntime Logs: {runtime_log}\n"
            f"IDE_PROBLEMS_WINDOW: {quality['problems']}\nCODE_UNDER_TEST:\n{code}",
            task="Verifying Functional & Structural Integrity",
            mission_id=mission_id
        )
        self._logger.log(state, "tester", f"Verification Loop {loop_i} Analysis", result)
        return result

    def _run_security(self, code, mission_id, loop_i, state) -> str:
        print("[SEC] Running security scan...")
        audit  = self._runtime.scan_security(code)
        result = self._auditor.execute(
            f"CODE:\n{code}\nSTATIC_SCAN_REPORT: {audit['summary']}",
            task="Performing Zero-Trust Security Audit",
            mission_id=mission_id
        )
        self._logger.log(state, "oncall-engineer", f"Security Audit Loop {loop_i}", result)
        return result
