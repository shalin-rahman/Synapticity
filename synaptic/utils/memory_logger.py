import asyncio
import os
import json
import time
from synaptic.config import settings


class MemoryLogger:
    """
    Logs AI conversations for troubleshooting and auditing. (raw LLM transcripts (System, User Prompt, Output) for deep debugging,
    auditing, and potential model fine-tuning datasets.)
    """

    @staticmethod
    async def log_interaction(
        mission_id: str,
        agent_name: str,
        task: str,
        provider: str,
        system_instruction: str,
        prompt: str,
        result: str,
    ):
        """Append the raw AI interaction to a JSON Lines file (non-blocking)."""
        if not mission_id:
            return

        memory_dir      = os.path.join(settings.WORKSPACE_PATH, mission_id, "memory")
        transcript_file = os.path.join(memory_dir, "transcript.jsonl")

        payload = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent_name,
            "task": task,
            "provider": provider,
            "input": {
                "system": system_instruction,
                "prompt": prompt,
            },
            "output": result,
        }

        def _write():
            os.makedirs(memory_dir, exist_ok=True)
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        try:
            await asyncio.to_thread(_write)
        except Exception:
            pass  # fail silently for background logging
