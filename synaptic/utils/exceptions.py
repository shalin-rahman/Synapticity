class SynapticError(Exception):
    """Base exception for all synaptic framework errors."""
    pass

class ConfigurationError(SynapticError):
    """Raised when environment or settings are misconfigured."""
    pass

class ModelProviderError(SynapticError):
    """Raised when an LLM provider (Gemini/Ollama) fails."""
    pass

class WorkflowError(SynapticError):
    """Raised when a mission lifecycle step fails."""
    pass

class SecurityAuditError(SynapticError):
    """Raised when a security guardrail is breached."""
    pass
