import json
import os
import time
from google import genai
from google.api_core import exceptions
from .base import AbstractModel
from synaptic.config import settings
from synaptic.utils.exceptions import ConfigurationError, ModelProviderError
from synaptic.utils.logger import synaptic_log

class GeminiAdapter(AbstractModel):
    """
    synaptic Adapter for Google Gemini.
    Handles high-level strategy and security auditing.
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
        """Swaps to the next key in the pool to circumvent rate limits."""
        if not self.keys: return
        self.index = (self.index + 1) % len(self.keys)
        with open(settings.TRACKER_FILE, "w") as f:
            json.dump({"index": self.index}, f)
        self.client = genai.Client(api_key=self.keys[self.index])
        synaptic_log.warning(f"Rotating Gemini API Key to account index: {self.index}")
        print(f"🔄 synaptic Rotation: Active Account {self.index + 1}")

    def generate(self, system_instruction: str, prompt: str) -> str:
        """
        Generates content from Gemini with built-in RPM management and rotation.
        """
        if not self.client:
            raise ConfigurationError(
                "Gemini API keys are missing in your .env file. "
                "Please add GEMINI_KEY_1 through GEMINI_KEY_5."
            )

        while True:
            try:
                # Enforce configured sleep buffer to respect 15 RPM limits
                time.sleep(settings.SLEEP_BUFFER)
                
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=f"{system_instruction}\n\nTask: {prompt}"
                )
                self._update_log()
                return response.text
                
            except exceptions.ResourceExhausted:
                # Hot-swap to the next account when quota is hit
                self.rotate()
            except Exception as e:
                raise ModelProviderError(f"Gemini API failed: {e}")

    def _update_log(self):
        log_file = settings.USAGE_LOG_FILE
        today = time.strftime("%Y-%m-%d")
        data = {}
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f: data = json.load(f)
            except: pass
        data[today] = data.get(today, 0) + 1
        with open(log_file, "w") as f: json.dump(data, f)
