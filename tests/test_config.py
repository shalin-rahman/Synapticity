import os
from synaptic.config import settings

def test_config_version():
    """Verify system versioning."""
    assert settings.VERSION == "3.3.0"

def test_key_sanitization():
    """Ensure placeholder keys are filtered out."""
    os.environ["GEMINI_KEY_1"] = "your_key_here"
    # settings is a singleton, so we check if the property handles it
    assert "your_key_here" not in settings.GEMINI_KEYS

def test_path_configuration():
    """Verify internal path mapping."""
    assert settings.AGENT_PATH == "agents"
    assert settings.WORKSPACE_PATH == "workspace"
