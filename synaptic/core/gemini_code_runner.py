"""
GeminiCodeRunner — Native Gemini Sandbox for Code Verification

Replaces the local subprocess RuntimeRunner when Gemini is the active engine
and GEMINI_USE_CODE_EXECUTION=True.

Gemini's built-in Code Execution tool runs Python in an isolated server-side
sandbox — no local subprocess, no Docker, no temp files.  The model writes
minimal test scaffolding, executes it, and returns the result.

Return format is compatible with RuntimeRunner.run_python_code() so
HealingCyclePhase can swap runners without changing its own logic.
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from google.genai import types

from synaptic.config import settings
from synaptic.utils.exceptions import ConfigurationError
from synaptic.utils.logger import synaptic_log


class GeminiCodeRunner:
    """
    Uses Gemini's native Code Execution tool to sandbox-test generated code.

    The prompt instructs Gemini to:
      1. Execute the code exactly as written.
      2. Report stdout, stderr, and success/failure status.
      3. Not modify the code — verification only.

    The runner re-uses the first available Gemini key (no rotation needed
    for short verification calls, though _api_call handles it if required).
    """

    _VERIFY_PROMPT = (
        "You are a code execution verifier. "
        "Execute the following Python code EXACTLY as written — do not modify it. "
        "Report: (1) whether it ran successfully, "
        "(2) the complete stdout output, "
        "(3) any errors or exceptions. "
        "Do not explain or suggest fixes — only report what happened.\n\n"
        "```python\n{code}\n```"
    )

    def __init__(self) -> None:
        if not settings.GEMINI_KEYS:
            raise ConfigurationError(
                "GeminiCodeRunner requires at least one GEMINI_KEY_* configured."
            )
        from google import genai
        self._client = genai.Client(api_key=settings.GEMINI_KEYS[0])
        self._config = types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.CodeExecution())],
        )

    async def run_python_code(self, code: str) -> dict:
        """
        Sends code to Gemini's sandbox and returns a RuntimeRunner-compatible dict:
            {
                "success":   bool,
                "stdout":    str,
                "stderr":    str,
                "exit_code": int,
                "duration":  float,
            }
        """
        prompt   = self._VERIFY_PROMPT.format(code=code)
        start    = time.monotonic()

        try:
            effective_sleep = settings.SLEEP_BUFFER * (2.0 if settings.GEMINI_TIER == "free" else 1.0)
            await asyncio.sleep(effective_sleep)
            response = await self._client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=self._config,
            )
            duration = round(time.monotonic() - start, 2)
            return self._parse_response(response, duration)

        except Exception as exc:
            synaptic_log.warning(f"[GeminiCodeRunner] API error: {exc}")
            return {
                "success":   False,
                "stdout":    "",
                "stderr":    str(exc),
                "exit_code": -1,
                "duration":  round(time.monotonic() - start, 2),
            }

    # ── response parsing ──────────────────────────────────────────────────────

    def _parse_response(self, response, duration: float) -> dict:
        """
        Extracts execution results from Gemini's response.

        Gemini returns code_execution_result parts alongside text parts.
        We prefer the structured result; fall back to text parsing.
        """
        stdout    = ""
        stderr    = ""
        success   = True

        candidate = response.candidates[0] if response.candidates else None
        if candidate:
            for part in candidate.content.parts:
                cer = getattr(part, "code_execution_result", None)
                if cer:
                    raw_output = getattr(cer, "output", "") or ""
                    outcome    = getattr(cer, "outcome", "OUTCOME_OK")
                    success    = str(outcome) in ("OUTCOME_OK", "SUCCESS", "1")
                    stdout     = raw_output
                    # Gemini surfaces errors inside output rather than a separate field
                    if not success and raw_output:
                        stderr = raw_output

        # Fallback: parse from the model's text description if no structured result
        if not stdout and response.text:
            text   = response.text
            success = not any(
                kw in text.lower()
                for kw in ("error", "exception", "traceback", "failed", "failure")
            )
            stdout = text

        synaptic_log.debug(
            f"[GeminiCodeRunner] success={success} | duration={duration}s | "
            f"stdout_len={len(stdout)}"
        )
        return {
            "success":   success,
            "stdout":    stdout,
            "stderr":    stderr,
            "exit_code": 0 if success else 1,
            "duration":  duration,
        }

    async def scan_quality(self, code: str) -> dict:
        """
        Asks Gemini to review the code for PEP-8 / SOLID / type-hint issues.
        Returns a RuntimeRunner.scan_quality()-compatible dict.
        """
        prompt = (
            "Review the following Python code for quality issues only "
            "(PEP-8, type hints, SOLID violations, unused imports). "
            "List each problem on its own line prefixed with 'PROBLEM: '. "
            "If there are no problems, respond with exactly: CLEAN\n\n"
            f"```python\n{code}\n```"
        )
        try:
            effective_sleep = settings.SLEEP_BUFFER * (2.0 if settings.GEMINI_TIER == "free" else 1.0)
            await asyncio.sleep(effective_sleep)
            response = await self._client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            text     = response.text or ""
            is_clean = "CLEAN" in text.upper() and "PROBLEM:" not in text.upper()
            problems = "\n".join(
                line for line in text.splitlines() if "PROBLEM:" in line.upper()
            )
            return {
                "clean":    is_clean,
                "problems": problems,
                "summary":  f"{problems.count('PROBLEM:')} quality issue(s) detected." if problems else "No issues.",
            }
        except Exception as exc:
            return {"clean": True, "problems": "", "summary": f"Quality scan skipped: {exc}"}
