"""
Ollama Local Model Adapter
Implements high-performance local inference for coding and testing tasks.
"""

import requests
from .base import AbstractModel
from synaptic.config import settings
from synaptic.utils.exceptions import ModelProviderError

class OllamaAdapter(AbstractModel):
    """
    synaptic Adapter for Ollama (Local Execution).
    Enforces privacy and high-throughput coding without API costs.
    """
    
    def __init__(self):
        self.url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL

    def generate(self, system_instruction: str, prompt: str) -> str:
        """
        Executes a generation request with official system-role support.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.2, # Low temperature for precise coding
                "num_predict": 4096, # Max tokens
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json().get('response', '')
            if not result:
                raise ModelProviderError("Ollama returned an empty response.")
            return result
            
        except requests.exceptions.Timeout:
            raise ModelProviderError("Ollama connection timed out. Is the model loaded?")
        except requests.exceptions.ConnectionError:
            raise ModelProviderError("Could not connect to Ollama. Is it running on 'ollama serve'?")
        except Exception as e:
            raise ModelProviderError(f"Local LLM failed: {e}")
