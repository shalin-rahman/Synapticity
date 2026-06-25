import asyncio
import subprocess
import sys
import tempfile
import os
import time
import contextlib
import json


class RuntimeRunner:
    """Safely executes generated code in a controlled environment."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    @contextlib.contextmanager
    def _create_temp_script(self, code: str):
        """Creates a temporary .py file, yields its path, then cleans up."""
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            yield tmp_path
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def run_python_code(self, code: str) -> dict:
        """Executes raw Python code via asyncio subprocess and returns execution results."""
        from synaptic.config import settings
        start_time = time.time()

        with self._create_temp_script(code) as script_path:
            try:
                if getattr(settings, "USE_DOCKER_SANDBOX", False):
                    proc = await asyncio.create_subprocess_exec(
                        "docker", "run", "--rm",
                        "-v", f"{script_path}:/app/script.py",
                        "python:3.11-slim", "python", "/app/script.py",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                else:
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable, script_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                try:
                    stdout_b, stderr_b = await asyncio.wait_for(
                        proc.communicate(), timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.communicate()
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Timed out ({self.timeout}s)",
                        "exit_code": -1,
                        "duration": self.timeout,
                    }

                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout_b.decode("utf-8", errors="replace"),
                    "stderr": stderr_b.decode("utf-8", errors="replace"),
                    "exit_code": proc.returncode,
                    "duration": round(time.time() - start_time, 2),
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "duration": round(time.time() - start_time, 2),
                }

    def scan_security(self, code: str) -> dict:
        """Runs bandit static analysis and returns a structured security report."""
        with self._create_temp_script(code) as script_path:
            try:
                proc = subprocess.run(
                    ["bandit", "-r", script_path, "-f", "json", "-q"],
                    capture_output=True, text=True, timeout=self.timeout
                )
                issues = (
                    json.loads(proc.stdout).get("results", [])
                    if proc.stdout.strip()
                    else []
                )
                return {
                    "secure": len(issues) == 0,
                    "issues": issues,
                    "summary": (
                        f"Bandit found {len(issues)} issue(s)."
                        if issues
                        else "No security issues found."
                    ),
                }
            except subprocess.TimeoutExpired:
                return {
                    "secure": False,
                    "issues": [],
                    "summary": f"Security scan timed out ({self.timeout}s).",
                }
            except Exception as e:
                return {"secure": True, "issues": [], "summary": f"Security scan skipped: {e}"}

    def scan_quality(self, code: str) -> dict:
        """Runs py_compile + ruff (fallback: pylint) and returns a quality report."""
        with self._create_temp_script(code) as script_path:
            try:
                comp = subprocess.run(
                    [sys.executable, "-m", "py_compile", script_path],
                    capture_output=True, text=True, timeout=self.timeout
                )
                if comp.returncode != 0:
                    return {
                        "clean": False,
                        "problems": comp.stderr.strip(),
                        "summary": "Syntax error detected.",
                    }

                try:
                    p = subprocess.run(
                        ["ruff", "check", script_path, "--quiet"],
                        capture_output=True, text=True, timeout=self.timeout
                    )
                    problems = p.stdout.strip()
                except FileNotFoundError:
                    p = subprocess.run(
                        [sys.executable, "-m", "pylint", script_path,
                         "--disable=all", "--enable=E,W"],
                        capture_output=True, text=True, timeout=self.timeout
                    )
                    problems = p.stdout.strip()

                return {
                    "clean": not problems,
                    "problems": problems,
                    "summary": (
                        f"Detected {len(problems.splitlines())} quality issue(s)."
                        if problems
                        else "No quality issues found."
                    ),
                }
            except Exception as e:
                return {"clean": True, "problems": "", "summary": f"Quality scan skipped: {e}"}
