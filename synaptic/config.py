from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from typing import List

class Settings(BaseSettings):
    """
    Global configuration for the The State of Intelligent Connection.
    Values can be overridden via .env file or environment variables.
    """
    
    # --- synaptic Core Identity ---
    VERSION: str = "2.0.0"
    
    # --- Gemini API Configuration ---
    # We will compute the list of keys dynamically
    GEMINI_MODEL: str = "gemini-3-flash"
    SLEEP_BUFFER: float = 4.0 # Seconds between calls
    
    # --- Local LLM (Ollama) Configuration ---
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    
    # --- Path Configuration ---
    AGENT_PATH: str = "agents"
    SKILL_PATH: str = "skills"
    WORKSPACE_PATH: str = "workspace"
    
    # --- Workflow Guardrails ---
    MAX_RETRY_ATTEMPTS: int = 3
    INTERACTIVE_MODE: bool = True 
    
    # --- Persona Filenames ---
    AGENT_ORCHESTRATOR: str = "orchestrator.md"
    AGENT_PM: str = "product-manager.md"
    AGENT_SWE: str = "software-engineer.md"
    AGENT_QA: str = "tester.md"
    AGENT_SECURITY: str = "oncall-engineer.md"
    AGENT_DOCS: str = "writer.md"
    
    # --- Persistent State ---
    TRACKER_FILE: str = "tracker.json"
    USAGE_LOG_FILE: str = "usage_log.json"
    STATE_FILE: str = "mission_state.json"
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def GEMINI_KEYS(self) -> List[str]:
        """Provides a filtered list of sanitized API keys."""
        keys = []
        # Search for GEMINI_KEY_1 through GEMINI_KEY_10
        for i in range(1, 11):
            key = os.getenv(f"GEMINI_KEY_{i}")
            if key and "your_key" not in key and len(key) > 5:
                keys.append(key)
        return keys

    @property
    def IS_HEALTHY(self) -> bool:
        """System health check: true if core credentials exist."""
        return len(self.GEMINI_KEYS) > 0

settings = Settings()
