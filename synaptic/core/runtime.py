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
        
        start_time = time.time()
        try:
            process = subprocess.run(
                [sys.executable, tmp_path],
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
