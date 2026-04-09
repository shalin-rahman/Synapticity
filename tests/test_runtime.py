import pytest
from synaptic.core.runtime import RuntimeRunner

@pytest.fixture
def runner():
    return RuntimeRunner(timeout=2)

def test_code_execution_success(runner):
    """Test successful python execution."""
    code = "print('Hello synaptic')"
    result = runner.run_python_code(code)
    assert result["success"] is True
    assert "Hello synaptic" in result["stdout"]

def test_code_execution_failure(runner):
    """Test python execution with syntax error."""
    code = "print('Hello synaptic'" # Missing parenthesis
    result = runner.run_python_code(code)
    assert result["success"] is False
    assert "SyntaxError" in result["stderr"]

def test_security_scan_skip_if_missing(runner):
    """Ensure scanner gracefully handles missing dependencies."""
    result = runner.scan_security("print('safe')")
    # Should return secure=True (fail-open) if bandit is missing
    assert result["secure"] is True
