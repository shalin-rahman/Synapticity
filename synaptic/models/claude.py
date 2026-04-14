import requests
import json
from synaptic.config import settings
from synaptic.models.base import AbstractModel
from synaptic.utils.exceptions import ModelProviderError

class ClaudeAdapter(AbstractModel):
    """
    Adapter for Anthropic's Claude models.
    Directly handles API requests via the 'requests' library to keep dependencies minimal.
    """

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.url = "https://api.anthropic.com/v1/messages"

        if not self.api_key:
            # Fallback check for common env naming
            import os
            self.api_key = os.getenv("CLAUDE_API_KEY", "")

    def generate(self, system_instruction: str, prompt: str) -> str:
        """Sends a request to Claude and returns the text response."""
        if not self.api_key:
            raise ModelProviderError("Claude API Key is missing. Set ANTHROPIC_API_KEY in your .env file.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": self.model,
            "system": system_instruction,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.5
        }

        try:
            response = requests.post(self.url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            payload = response.json()
            # Extract content from Claude's response format: content[0].text
            if "content" in payload and len(payload["content"]) > 0:
                return payload["content"][0]["text"]
            
            raise ModelProviderError(f"Unexpected Claude API response format: {payload}")

        except requests.exceptions.HTTPError as he:
            error_data = response.json() if response.text else "No error details available."
            raise ModelProviderError(f"Claude API HTTP Error: {he} | Details: {error_data}")
        except Exception as e:
            raise ModelProviderError(f"Failed to reach Claude API: {e}")
