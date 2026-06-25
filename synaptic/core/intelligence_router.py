"""
Intelligence Router — determines the optimal primary/fallback model pair.
Single Responsibility: isolates model selection logic from the orchestration engine.
"""
import os
import json
from synaptic.config import settings
from synaptic.models.gemini import GeminiAdapter
from synaptic.models.ollama import OllamaAdapter
from synaptic.models.claude import ClaudeAdapter
from synaptic.core.analytics import PerformanceAnalytics
from synaptic.utils.exceptions import ConfigurationError

class IntelligenceRouter:
    """Handles logic for model selection, health checks, and autonomous rotation."""

    def __init__(self):
        self._analytics = PerformanceAnalytics()

    def resolve(self) -> tuple:
        """Determines the best primary and fallback model adapters based on config and history."""
        # Lazy-load adapters only when needed to avoid unnecessary resource usage
        _gemini = None
        _claude = None

        def get_gemini():
            nonlocal _gemini
            if _gemini is None and settings.GEMINI_ACTIVE:
                # Upgrade to GeminiToolAdapter when function calling is enabled
                if settings.GEMINI_USE_FUNCTION_CALLING or settings.GEMINI_USE_CODE_EXECUTION:
                    from synaptic.models.gemini_tool import GeminiToolAdapter
                    from synaptic.core.tool_dispatcher import SynapticToolDispatcher
                    from synaptic.core.skill_registry import SkillRegistry
                    dispatcher = SynapticToolDispatcher(skill_registry=SkillRegistry())
                    _gemini = GeminiToolAdapter(dispatcher=dispatcher)
                else:
                    _gemini = GeminiAdapter()
            return _gemini

        def get_claude():
            nonlocal _claude
            if _claude is None and settings.CLAUDE_ACTIVE:
                _claude = ClaudeAdapter()
            return _claude

        cloud = get_claude() if settings.CLAUDE_ACTIVE else (get_gemini() if settings.GEMINI_ACTIVE else None)

        primary, fallback = None, None
        if settings.OLLAMA_ACTIVE:
            primary = OllamaAdapter(settings.OLLAMA_MODEL)
            # 1. Try local fallback first
            if settings.OLLAMA_FALLBACK_MODEL:
                fallback = OllamaAdapter(settings.OLLAMA_FALLBACK_MODEL)
            # 2. Revert to cloud if no local fallback exists
            else:
                fallback = cloud
        elif cloud:
            primary, fallback = cloud, (get_gemini() if settings.CLAUDE_ACTIVE and settings.GEMINI_ACTIVE else None)
        else:
            raise ConfigurationError("No intelligence engines available. Update .env.")

        return self._apply_reliability_rotation(primary, fallback)

    def _apply_reliability_rotation(self, primary, fallback):
        """Swaps primary for fallback if historical reliability is too low."""
        if not fallback or not os.path.exists(self._analytics.stats_file):
            return primary, fallback

        try:
            with open(self._analytics.stats_file, "r", encoding="utf-8") as r:
                stats = json.load(r)
            
            model_key = type(primary).__name__.replace("Adapter", "")
            if model_key == "Ollama": 
                model_key = settings.OLLAMA_MODEL
            
            m_stats = stats.get("agent_metrics", {}).get(model_key)
            if m_stats and m_stats["total"] >= 3:
                reliability = (1 - m_stats["failures"]/m_stats["total"]) * 100
                if reliability < 40:
                    print(f"[WARN] {model_key} reliability is low ({reliability}%). Rotating to fallback...")
                    return fallback, None # Promote fallback to primary
        except:
            pass

        return primary, fallback

