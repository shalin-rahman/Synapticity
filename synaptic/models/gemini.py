"""
Gemini Model Adapter (Async Version)
Handles high-level strategy and security auditing via Google Gemini API.
"""

import json
import os
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

    def rotate(self):
        """Swaps to the next key in the pool (Synchronous state update)."""
        if not self.keys: return
        self.index = (self.index + 1) % len(self.keys)
        with open(settings.TRACKER_FILE, "w") as f:
            json.dump({"index": self.index}, f)
        self.client = genai.Client(api_key=self.keys[self.index])
        synaptic_log.warning(f"Rotating Gemini API Key index: {self.index}")

    async def generate(self, system_instruction: str, prompt: str) -> str:
        """Asynchronous generation with built-in rate-limit back-off."""
        if not self.client:
            raise ConfigurationError("Gemini API keys missing.")

        while True:
            try:
                # Respect rate limits via non-blocking sleep
                await asyncio.sleep(settings.SLEEP_BUFFER)
                
                # Use the asynchronous entry point from the SDK
                response = await self.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=f"{system_instruction}\n\nTask: {prompt}"
                )
                return response.text
                
            except Exception as e:
                err_str = str(e).upper()
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    synaptic_log.warning(f"Quota Hit. Rotating...")
                    self.rotate()
                    if len(self.keys) <= 1:
                        await asyncio.sleep(20) # Back-off for single key
                    continue
                
                synaptic_log.error(f"Gemini API Error: {e}")
                raise ModelProviderError(f"Gemini failed: {e}")
