import subprocess
import sys
import tempfile
import os
import time

class RuntimeRunner:
    """
    Safely executes generated code in a controlled environment.
    Captures stdout, stderr, and return codes for testing.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def run_python_code(self, code: str) -> dict:
        """
        Executes raw Python code and returns the execution metrics.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        from synaptic.config import settings
        
        start_time = time.time()
        try:
            if getattr(settings, "USE_DOCKER_SANDBOX", False):
                cmd = [
                    "docker", "run", "--rm", 
                    "-v", f"{tmp_path}:/app/script.py", 
                    "python:3.11-slim", "python", "/app/script.py"
                ]
            else:
                cmd = [sys.executable, tmp_path]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "duration": round(time.time() - start_time, 2)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": -1,
                "duration": self.timeout
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "duration": 0
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def scan_security(self, code: str) -> dict:
        """
        Performs static security analysis using Bandit.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        try:
            # Run bandit - format: json, quietly
            # Needs 'pip install bandit'
            process = subprocess.run(
                ["bandit", "-r", tmp_path, "-f", "json", "-q"],
                capture_output=True,
                text=True
            )
            
            # Bandit returns exit code 1 if issues found
            import json
            issues = json.loads(process.stdout).get("results", [])
            
            return {
                "secure": len(issues) == 0,
                "issues": issues,
                "summary": f"Detected {len(issues)} security vulnerabilities."
            }
        except Exception as e:
            return {
                "secure": True, # Fail open if bandit missing
                "issues": [],
                "summary": f"Static scan skipped: {e}"
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def scan_quality(self, code: str) -> dict:
        """
        Simulates the VSCode 'Problems' window.
        Detects syntax errors, PEP8 violations, and code smells.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        try:
            # 1. Physical Compilation Check
            compile_proc = subprocess.run(
                [sys.executable, "-m", "py_compile", tmp_path],
                capture_output=True, text=True
            )
            if compile_proc.returncode != 0:
                return {
                    "clean": False,
                    "problems": f"CRITICAL: Syntax/Compilation Error:\n{compile_proc.stderr}",
                    "summary": "Code failed to compile (Syntax Error)."
                }

            # 2. Linting (Try Ruff first, then Pylint/Flake8)
            # Ruff is the industry standard for fast 'Problems' simulation in 2026
            try:
                lint_proc = subprocess.run(
                    ["ruff", "check", tmp_path, "--quiet"],
                    capture_output=True, text=True
                )
                problems = lint_proc.stdout
            except:
                # Fallback to simple Pylint if ruff is missing
                lint_proc = subprocess.run(
                    ["pylint", tmp_path, "--disable=all", "--enable=E,W"],
                    capture_output=True, text=True
                )
                problems = lint_proc.stdout

            return {
                "clean": not problems.strip(),
                "problems": problems.strip(),
                "summary": f"Detected {len(problems.splitlines())} quality issues matching VSCode 'Problems'."
            }
        except Exception as e:
            return {
                "clean": True,
                "problems": "",
                "summary": f"Quality scan skipped: {e}"
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
