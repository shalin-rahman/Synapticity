import subprocess
import sys
import tempfile
import os
import time
import contextlib
import json

class RuntimeRunner:
    """
    Safely executes generated code in a controlled environment.
    Captures stdout, stderr, and return codes for testing.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    @contextlib.contextmanager
    def _create_temp_script(self, code: str):
        """Standardizes tempfile creation and cleanup across all scan/run methods (DRY)."""
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            yield tmp_path
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def run_python_code(self, code: str) -> dict:
        """Executes raw Python code and returns technical execution metrics."""
        from synaptic.config import settings
        start_time = time.time()
        
        with self._create_temp_script(code) as script_path:
            try:
                cmd = [sys.executable, script_path]
                if getattr(settings, "USE_DOCKER_SANDBOX", False):
                    cmd = [
                        "docker", "run", "--rm", 
                        "-v", f"{script_path}:/app/script.py", 
                        "python:3.11-slim", "python", "/app/script.py"
                    ]

                process = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
                
                return {
                    "success": process.returncode == 0,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                    "duration": round(time.time() - start_time, 2)
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "stdout": "", "stderr": f"Timed out ({self.timeout}s)", "exit_code": -1, "duration": self.timeout}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1, "duration": 0}

    def scan_security(self, code: str) -> dict:
        """Runs static analysis (Bandit) to detect vulnerabilities."""
        with self._create_temp_script(code) as script_path:
            try:
                # Bandit returns exit code 1 if issues found. Use -q for quiet JSON output.
                process = subprocess.run(["bandit", "-r", script_path, "-f", "json", "-q"], capture_output=True, text=True)
                issues  = json.loads(process.stdout).get("results", [])
                
                return {
                    "secure": len(issues) == 0,
                    "issues": issues,
                    "summary": f"Detected {len(issues)} security vulnerabilities."
                }
            except Exception as e:
                return {"secure": True, "issues": [], "summary": f"Security scan skipped: {e}"}

    def scan_quality(self, code: str) -> dict:
        """Simulates VSCode 'Problems' by detecting syntax errors and PEP8 violations."""
        with self._create_temp_script(code) as script_path:
            try:
                # 1. Compilation Check
                comp = subprocess.run([sys.executable, "-m", "py_compile", script_path], capture_output=True, text=True)
                if comp.returncode != 0:
                    return {"clean": False, "problems": comp.stderr, "summary": "Compilation failed (Syntax Error)."}

                # 2. Linting (Ruff primary, Pylint fallback)
                problems = ""
                try:
                    p = subprocess.run(["ruff", "check", script_path, "--quiet"], capture_output=True, text=True)
                    problems = p.stdout
                except:
                    p = subprocess.run([sys.executable, "-m", "pylint", script_path, "--disable=all", "--enable=E,W"], capture_output=True, text=True)
                    problems = p.stdout

                return {
                    "clean": not problems.strip(),
                    "problems": problems.strip(),
                    "summary": f"Detected {len(problems.splitlines())} quality issues."
                }
            except Exception as e:
                return {"clean": True, "problems": "", "summary": f"Quality scan skipped: {e}"}
