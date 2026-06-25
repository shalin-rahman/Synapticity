"""
Ollama Local Model Adapter (Async Version)
Implements high-performance local inference with auto-service and auto-pull management.
"""

import httpx
import subprocess
import asyncio
import os
import json
import time
from .base import AbstractModel
from synaptic.config import settings
from synaptic.utils.exceptions import ModelProviderError
from synaptic.utils.logger import synaptic_log

class OllamaAdapter(AbstractModel):
    """
    Synaptic Adapter for Ollama (Local Execution).
    Now fully asynchronous for high-density workflow orchestration.
    """
    
    def __init__(self, model_name: str = None):
        self.url = settings.OLLAMA_URL
        self.pull_url = self.url.replace("/generate", "/pull")
        self.tags_url = self.url.replace("/generate", "/tags")
        self.model = model_name or settings.OLLAMA_MODEL
        self._servicing = False
        self._client = httpx.AsyncClient(timeout=1800.0)
        
        # Non-blocking warm-up remains in background thread to avoid event loop contention on start
        import threading
        threading.Thread(target=self._pre_warm_sync, daemon=True).start()

    def _pre_warm_sync(self):
        """Synchronous wrapper for initial service check and model pull."""
        try:
            self._ensure_service_sync()
            self._ensure_model_exists_sync()
            # Send warm-up request
            import requests
            payload = {
                "model": self.model,
                "prompt": "",
                "stream": False,
                "keep_alive": -1
            }
            requests.post(self.url, json=payload, timeout=10)
            synaptic_log.info(f"Ollama Warm-up initiated: {self.model}")
        except Exception as e:
            synaptic_log.debug(f"Pre-warm failed: {e}")

    def _ensure_service_sync(self):
        """Checks if Ollama is running, starts it if not (Blocking)."""
        if self._servicing: return
        try:
            import requests
            requests.get(self.tags_url, timeout=1)
            self._servicing = True
        except:
            self._start_service_cli()

    def _ensure_model_exists_sync(self):
        """Ensures the model is available locally (Blocking if pulling)."""
        import requests
        try:
            res = requests.get(self.tags_url, timeout=2)
            if res.status_code == 200:
                models = [m['name'] for m in res.json().get('models', [])]
                if self.model in models or f"{self.model}:latest" in models:
                    return
            
            print(f"[DIR] Synaptic: Local brain is empty. Pulling '{self.model}'...")
            payload = {"name": self.model, "stream": False}
            requests.post(self.pull_url, json=payload, timeout=900)
        except Exception as e:
            synaptic_log.warning(f"Model pull failed: {e}")

    def _start_service_cli(self):
        """Platform-specific service bootstrapper."""
        paths = ["ollama"]
        if os.name == 'nt':
            appdata = os.getenv("LOCALAPPDATA", "")
            paths.append(os.path.join(appdata, "Programs", "Ollama", "ollama.exe"))
            paths.append(r"C:\Program Files\Ollama\ollama.exe")
        
        for path in paths:
            try:
                if os.name == 'nt':
                    subprocess.Popen([path, "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[AI] Waking up Local Brain (Ollama)...")
                time.sleep(10)
                self._servicing = True
                return
            except:
                continue

    async def generate(self, system_instruction: str, prompt: str) -> str:
        """Asynchronous generation entry point."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
                "num_ctx": 4096
            }
        }
        
        try:
            return await self._make_request_async(payload)
        except Exception as e:
            synaptic_log.error(f"Async Local AI Error: {repr(e)}")
            raise ModelProviderError(f"Ollama Generation Failed: {e}")

    async def _make_request_async(self, payload: dict, is_retry: bool = False) -> str:
        try:
            response = await self._client.post(self.url, json=payload)
            response.raise_for_status()

            data = response.json()
            result = data.get('response', '')

            if not result and not is_retry:
                await asyncio.sleep(3)
                return await self._make_request_async(payload, is_retry=True)

            return result
        except (httpx.ConnectError, httpx.HTTPStatusError) as e:
            if not is_retry:
                # In a real async system, we'd want a non-blocking service restarter
                # but for now we fallback to the sync service check
                self._ensure_service_sync()
                return await self._make_request_async(payload, is_retry=True)
            raise
