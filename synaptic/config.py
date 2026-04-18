from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from typing import List
from dotenv import load_dotenv

# Explicitly load .env into system environment
load_dotenv()

class Settings(BaseSettings):
    """
    Global configuration for Synapticity.
    Values can be overridden via .env file or environment variables.
    """
    
    # --- Core Identity ---
    VERSION: str = "3.3.0"  # Advanced features and faster performance
    
    # --- Gemini API Configuration ---
    GEMINI_ACTIVE: bool = False
    GEMINI_MODEL: str = "gemini-2.0-flash"
    SLEEP_BUFFER: float = 4.0 # Seconds between calls
    
    # --- Local LLM (Ollama) Configuration ---
    OLLAMA_ACTIVE: bool = True
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "")

    # --- Claude (Anthropic) Configuration ---
    CLAUDE_ACTIVE: bool = False
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20240620"
    
    # --- Path Configuration ---
    AGENT_PATH: str = "agents"
    SKILL_PATH: str = "skills"
    WORKSPACE_PATH: str = "workspace"
    
    # --- Workflow Guardrails ---
    MAX_RETRY_ATTEMPTS: int = 3
    INTERACTIVE_MODE: bool = True 
    HEARTBEAT_INTERVAL: int = 30
    ENABLE_HOT_RELOAD: bool = True  # FileSystem Watcher toggle for SkillRegistry
    
    # --- Persona Filenames ---
    AGENT_PM: str = "product-manager.md"
    AGENT_SWE: str = "software-engineer.md"
    AGENT_QA: str = "tester.md"
    AGENT_SECURITY: str = "oncall-engineer.md"
    AGENT_DOCS: str = "writer.md"
    AGENT_DEVOPS: str = "devops-engineer.md"
    
    # --- DevOps & Continuous Deployment ---
    GITHUB_USER: str = os.getenv("GITHUB_USER", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    USE_DOCKER_SANDBOX: bool = False
    ADMIN_PASSCODE: str = os.getenv("ADMIN_PASSCODE", "alpha-tango-77")
    
    # --- Persistent State ---
    TRACKER_FILE: str = "tracker.json"
    STATE_FILE: str = "mission_state.json"
    LOG_LEVEL: str = "INFO"
    
    # --- Phase 22: Sensory & Observability ---
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # --- Phase 23: High-Performance Engine ---
    USE_AGNO_ORCHESTRATOR: bool = False # Toggle for Agno micro-agent initialization
    
    # --- Phase 24: Deep Memory Persistence (Hippocampus) ---
    LOGSEQ_GRAPH_PATH: str = os.getenv("LOGSEQ_GRAPH_PATH", "")
    SYNAPTIC_BUFFER_SIZE: int = 256000 # 256K context limit
    
    # --- Phase 25: Offline Consolidation ---
    ENABLE_DREAM_STATE: bool = False
    OFFLINE_LEARNING_THRESHOLD: float = 0.20 # 20% failure rate triggers local fine-tune
    UNSLOTH_VRAM_TARGET: int = 24 # Targeted at 24GB GPUs

    @property
    def ANTHROPIC_API_KEY(self) -> str:
        """Retrieves the Anthropic API key from environment."""
        return os.getenv("ANTHROPIC_API_KEY", "")
    
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
        """System health check: true if core engines are configured."""
        return self.OLLAMA_ACTIVE or len(self.GEMINI_KEYS) > 0 or self.CLAUDE_ACTIVE

settings = Settings()
