"""
Gemini Model Adapter (Async Version)
Handles high-level strategy and security auditing via Google Gemini API.
"""

import json
import os
import time
import asyncio
from google import genai
from .base import AbstractModel
from synaptic.config import settings
from synaptic.utils.exceptions import ConfigurationError, ModelProviderError
from synaptic.utils.logger import synaptic_log

class GeminiAdapter(AbstractModel):
    """
    Synaptic Adapter for Google Gemini.
    Features automated multi-key rotation and rate-limit management.
    Now fully asynchronous for high-performance mission orchestration.
    """
    
    def __init__(self):
        self.keys = settings.GEMINI_KEYS
        self.index = self._load_session()
        self.client = self._init_client()
        self._rotate_lock = asyncio.Lock()
        self._key_cooldowns = {}  # {index: cooldown_until_timestamp}

    def _load_session(self) -> int:
        if os.path.exists(settings.TRACKER_FILE):
            try:
                with open(settings.TRACKER_FILE, "r") as f:
                    return json.load(f).get("index", 0)
            except:
                return 0
        return 0

    def _init_client(self):
        if not self.keys:
            return None
        return genai.Client(api_key=self.keys[self.index])

    async def rotate(self):
        """Swaps to the next key in the pool (async-safe state update)."""
        if not self.keys:
            return
        async with self._rotate_lock:
            self.index = (self.index + 1) % len(self.keys)
            await asyncio.to_thread(self._save_session)
            self.client = genai.Client(api_key=self.keys[self.index])
        synaptic_log.warning(f"Rotating Gemini API Key index: {self.index}")

    def _save_session(self):
        """Synchronous file I/O wrapper for session persistence."""
        with open(settings.TRACKER_FILE, "w") as f:
            json.dump({"index": self.index}, f)

    def _is_key_available(self, key_index: int) -> bool:
        """Checks if a key has passed its cooldown window."""
        cooldown_until = self._key_cooldowns.get(key_index, 0)
        return time.time() >= cooldown_until

    def _mark_key_exhausted(self, key_index: int, cooldown_seconds: float = 60.0):
        """Marks a key as exhausted until the cooldown window passes."""
        self._key_cooldowns[key_index] = time.time() + cooldown_seconds
        synaptic_log.warning(f"Key {key_index} exhausted. Cooldown for {cooldown_seconds}s.")

    async def _api_call(self, contents, config=None):
        """
        Protected helper: one API call with full rate-limit retry and key rotation.
        Used by both generate() and GeminiToolAdapter's agentic loop so rotation
        logic lives in exactly one place.
        """
        if not self.client:
            raise ConfigurationError("Gemini API keys missing.")

        attempts = 0
        max_attempts = len(self.keys) * 3 if self.keys else 1

        while attempts < max_attempts:
            attempts += 1

            if not self._is_key_available(self.index):
                synaptic_log.debug(f"Key {self.index} in cooldown. Rotating...")
                await self.rotate()
                continue

            try:
                effective_sleep = settings.SLEEP_BUFFER * (2.0 if settings.GEMINI_TIER == "free" else 1.0)
                await asyncio.sleep(effective_sleep)
                kwargs = {"model": settings.GEMINI_MODEL, "contents": contents}
                if config is not None:
                    kwargs["config"] = config
                return await self.client.aio.models.generate_content(**kwargs)

            except Exception as e:
                err_str = str(e).upper()
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    synaptic_log.warning(f"Quota Hit on key {self.index}. Rotating...")
                    self._mark_key_exhausted(self.index, cooldown_seconds=60.0)
                    await self.rotate()
                    if len(self.keys) <= 1 or all(
                        not self._is_key_available(i) for i in range(len(self.keys))
                    ):
                        backoff = min(20 * (2 ** (attempts - 1)), 300)
                        synaptic_log.warning(f"All keys exhausted. Backing off {backoff}s...")
                        await asyncio.sleep(backoff)
                    continue
                synaptic_log.error(f"Gemini API Error: {e}")
                raise ModelProviderError(f"Gemini failed: {e}")

        raise ModelProviderError(
            "Gemini failed: All API keys exhausted after maximum rotation attempts."
        )

    async def generate(self, system_instruction: str, prompt: str) -> str:
        """Asynchronous generation with built-in rate-limit back-off."""
        response = await self._api_call(
            contents=f"{system_instruction}\n\nTask: {prompt}"
        )
        return response.text

