"""
Ollama Local Model Adapter
Implements high-performance local inference with auto-service and auto-pull management.
"""

import requests
import subprocess
import time
import os
import json
from .base import AbstractModel
from synaptic.config import settings
from synaptic.utils.exceptions import ModelProviderError
from synaptic.utils.logger import synaptic_log

class OllamaAdapter(AbstractModel):
    """
    Synaptic Adapter for Ollama (Local Execution).
    Handles service health and automated model pulling.
    """
    
    def __init__(self):
        self.url = settings.OLLAMA_URL
        self.pull_url = self.url.replace("/generate", "/pull")
        self.tags_url = self.url.replace("/generate", "/tags")
        self.model = settings.OLLAMA_MODEL
        self._servicing = False
        
        # Initiate non-blocking warp-speed load
        import threading
        threading.Thread(target=self.pre_warm, daemon=True).start()

    def pre_warm(self):
        """Sends a warm-up signal to Ollama to pre-load model weights into VRAM."""
        try:
            # Check service first
            self._ensure_service()
            # Non-blocking check for model existence
            self._ensure_model_exists()
            # Send an empty request with -1 keep_alive to lock model in memory
            payload = {
                "model": self.model,
                "prompt": "",
                "template": "",
                "stream": False,
                "keep_alive": -1 # Keep model in memory indefinitely until server stops
            }
            requests.post(self.url, json=payload, timeout=5)
            synaptic_log.info(f"Ollama Warm-up initiated for {self.model}")
        except Exception as e:
            synaptic_log.debug(f"Pre-warm failed: {e}")

    def _ensure_model_exists(self):
        """Checks if the configured model is pulled, otherwise initiates pull."""
        try:
            res = requests.get(self.tags_url, timeout=5)
            if res.status_code == 200:
                models = [m['name'] for m in res.json().get('models', [])]
                if self.model in models or f"{self.model}:latest" in models:
                    return
            
            print(f"[DIR] Synaptic: Local brain is empty. Pulling '{self.model}' (7B)...")
            synaptic_log.info(f"Pulling local model: {self.model}")
            
            payload = {"name": self.model, "stream": False}
            res = requests.post(self.pull_url, json=payload, timeout=900)
            res.raise_for_status()
            print(f"[OK] Model {self.model} is now live. Calibrating memory...")
            time.sleep(10) # Let the background loader finish
            
        except Exception as e:
            synaptic_log.warning(f"Model pull check/attempt failed: {e}")

    def _ensure_service(self):
        """Attempts to start Ollama in the background if unreachable."""
        if self._servicing: return
        try:
            requests.get(self.tags_url, timeout=1)
            self._servicing = True
            return
        except:
            pass

        try:
            paths = ["ollama"]
            if os.name == 'nt':
                appdata = os.getenv("LOCALAPPDATA", "")
                paths.append(os.path.join(appdata, "Programs", "Ollama", "ollama.exe"))
                paths.append(r"C:\Program Files\Ollama\ollama.exe")
                # Add common user-space install path
                paths.append(os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs", "Ollama", "ollama.exe"))

            for path in paths:
                try:
                    if os.name == 'nt':
                        # Check if path exists before running
                        import shutil
                        actual_path = shutil.which(path) or (path if os.path.exists(path) else None)
                        if not actual_path: continue
                        
                        subprocess.Popen([actual_path, "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        subprocess.Popen([path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    print("[AI] Waking up Local Brain (Ollama)...")
                    time.sleep(12) # Longer wait for cold boot
                    self._servicing = True
                    return
                except Exception as ex:
                    synaptic_log.debug(f"Failed to start Ollama at {path}: {ex}")
                    continue
        except Exception as e:
            synaptic_log.error(f"Failure during Service Discovery: {e}")

    def generate(self, system_instruction: str, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "keep_alive": -1,   # Ensure model remains in VRAM after generation
            "options": {
                "temperature": 0.1,  
                "num_predict": 2048, 
                "top_p": 0.9,
                "num_ctx": 8192,     
                "num_thread": 8      
            }
        }
        
        try:
            return self._make_request(payload)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            if status_code == 404 or isinstance(e, requests.exceptions.ConnectionError):
                self._ensure_service()
                self._ensure_model_exists()
                return self._make_request(payload, is_retry=True)
            raise ModelProviderError(f"Local AI critical failure: {e}")

    def _make_request(self, payload, is_retry=False):
        try:
            response = requests.post(self.url, json=payload, timeout=600) # 10 minute timeout for fresh model load
            response.raise_for_status()
            
            raw_data = response.json()
            result = raw_data.get('response', '')
            
            if not result:
                # If it's a success but empty, it might be loading. Retry once after a sleep.
                if not is_retry:
                    synaptic_log.warning("Ollama returned empty response. Could be loading. Retrying in 5s...")
                    time.sleep(5)
                    return self._make_request(payload, is_retry=True)
                
                # Capture specific Ollama error if available
                error_msg = raw_data.get('error', 'Ollama returned success but empty content.')
                synaptic_log.error(f"Empty local response. Payload: {payload['model']} | Error: {error_msg}")
                raise ModelProviderError(f"Local AI failed: {error_msg}")
                
            return result
        except requests.exceptions.Timeout:
            if not is_retry:
                print("[WARN] Local model is taking a long time to load. Retrying...")
                return self._make_request(payload, is_retry=True)
            raise ModelProviderError("Local model timed out twice. Check your system resources.")
