"""
Claude Model Adapter (Async Version)
Driver for Anthropic's Claude models.
"""

import httpx
import json
from synaptic.config import settings
from synaptic.models.base import AbstractModel
from synaptic.utils.exceptions import ModelProviderError

class ClaudeAdapter(AbstractModel):
    """
    Claude Adapter.
    Designed for fast, non-blocking requests.
    """

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.url = "https://api.anthropic.com/v1/messages"

    async def generate(self, system_instruction: str, prompt: str) -> str:
        """Asynchronously sends a request to Claude and returns the text response."""
        if not self.api_key:
            raise ModelProviderError("Claude API Key is missing. Set ANTHROPIC_API_KEY.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": self.model,
            "system": system_instruction,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "temperature": 0.5
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            try:
                response = await client.post(self.url, headers=headers, json=data)
                response.raise_for_status()
                
                payload = response.json()
                if "content" in payload and len(payload["content"]) > 0:
                    return payload["content"][0]["text"]
                
                raise ModelProviderError(f"Unexpected Claude format: {payload}")
            except Exception as e:
                raise ModelProviderError(f"Claude Connection Failed: {e}")
