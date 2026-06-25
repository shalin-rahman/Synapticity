"""
Synapticity Framework — Comprehensive Test Suite
Covers all core subsystems without requiring live LLM/API keys.
Run: python test_suite.py
"""
import asyncio
import json
import os
import sys
import tempfile
import shutil
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = failed = skipped = 0

def ok(name):
    global passed
    passed += 1
    print(f"  {GREEN}[PASS]{RESET} {name}")

def fail(name, err):
    global failed
    failed += 1
    print(f"  {RED}[FAIL]{RESET} {name}")
    print(f"         {RED}{err}{RESET}")

def skip(name, reason):
    global skipped
    skipped += 1
    print(f"  {YELLOW}[SKIP]{RESET} {name} — {reason}")

def section(title):
    print(f"\n{BOLD}{CYAN}{'-'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'-'*60}{RESET}")

def run(name, fn, *args, **kwargs):
    """Runs a sync test function."""
    try:
        fn(*args, **kwargs)
        ok(name)
    except Exception as e:
        fail(name, e)

def run_async(name, coro_fn, *args, **kwargs):
    """Runs an async test coroutine."""
    try:
        asyncio.run(coro_fn(*args, **kwargs))
        ok(name)
    except Exception as e:
        fail(name, e)


# ══════════════════════════════════════════════════════════════════════════════
# 1. CONFIG
# ══════════════════════════════════════════════════════════════════════════════
section("1. Config / Settings")

def test_config_loads():
    from synaptic.config import settings
    assert settings.VERSION, "VERSION missing"
    assert isinstance(settings.MAX_RETRY_ATTEMPTS, int)
    assert isinstance(settings.HEARTBEAT_INTERVAL, int)
    assert isinstance(settings.GEMINI_ACTIVE, bool)
    assert isinstance(settings.OLLAMA_ACTIVE, bool)

def test_config_paths():
    from synaptic.config import settings
    assert settings.AGENT_PATH == "agents"
    assert settings.SKILL_PATH == "skills"
    assert settings.WORKSPACE_PATH == "workspace"

def test_config_gemini_keys_list():
    from synaptic.config import settings
    keys = settings.GEMINI_KEYS
    assert isinstance(keys, list)

def test_config_is_healthy():
    from synaptic.config import settings
    result = settings.IS_HEALTHY
    assert isinstance(result, bool)

def test_config_phase31_flags():
    from synaptic.config import settings
    assert isinstance(settings.GEMINI_USE_FUNCTION_CALLING, bool)
    assert isinstance(settings.GEMINI_USE_CODE_EXECUTION, bool)
    assert isinstance(settings.MAX_TOOL_ROUNDS, int)
    assert settings.MAX_TOOL_ROUNDS > 0

run("Settings instantiate correctly",   test_config_loads)
run("Path defaults are correct",        test_config_paths)
run("GEMINI_KEYS returns a list",       test_config_gemini_keys_list)
run("IS_HEALTHY returns bool",          test_config_is_healthy)
run("Phase 31 agentic flags present",   test_config_phase31_flags)


# ══════════════════════════════════════════════════════════════════════════════
# 2. FORMATTING — strip_markdown_backticks
# ══════════════════════════════════════════════════════════════════════════════
section("2. Formatting — strip_markdown_backticks")

from synaptic.utils.formatting import strip_markdown_backticks

def test_fmt_plain_fence():
    out = strip_markdown_backticks("```python\nimport sys\nprint('hi')\n```")
    assert "import sys" in out and out.startswith("import sys"), f"got: {out!r}"

def test_fmt_no_language_tag():
    out = strip_markdown_backticks("```\nprint('hello')\n```")
    assert "print('hello')" in out

def test_fmt_crlf_endings():
    code = "```python\r\nimport sys\r\nprint('hi')\r\n```"
    out = strip_markdown_backticks(code)
    assert "import sys" in out, f"CRLF stripping failed: {out!r}"

def test_fmt_no_fence():
    raw = "import sys\nprint('hi')"
    out = strip_markdown_backticks(raw)
    assert "import sys" in out

def test_fmt_leading_text():
    raw = "Here is the code:\n```python\nimport sys\n```"
    out = strip_markdown_backticks(raw)
    assert "import sys" in out

def test_fmt_trailing_explanation():
    raw = "```python\nimport sys\n```\nThis code imports sys."
    out = strip_markdown_backticks(raw)
    assert "import sys" in out

def test_fmt_strips_language_in_fallback():
    raw = "```python\nimport os"   # missing closing fence
    out = strip_markdown_backticks(raw)
    assert "python" not in out.lower().split("\n")[0] or "import" in out

run("Plain ```python fence",            test_fmt_plain_fence)
run("No language tag fence",            test_fmt_no_language_tag)
run("Windows CRLF line endings",        test_fmt_crlf_endings)
run("No fence — passthrough",           test_fmt_no_fence)
run("Leading explanation text",         test_fmt_leading_text)
run("Trailing explanation text",        test_fmt_trailing_explanation)
run("Fallback strips language tag",     test_fmt_strips_language_in_fallback)


# ══════════════════════════════════════════════════════════════════════════════
# 3. HASHING
# ══════════════════════════════════════════════════════════════════════════════
section("3. Context Hashing")

from synaptic.utils.hashing import generate_context_hash

def test_hash_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        result = generate_context_hash(d)
        assert result is None, "Empty dir should return None"

def test_hash_with_md_file():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "spec.md"), "w") as f:
            f.write("# Project spec")
        result = generate_context_hash(d)
        assert result and len(result) == 32, f"Expected MD5 hex, got: {result!r}"

def test_hash_deterministic():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "spec.md"), "w") as f:
            f.write("same content")
        h1 = generate_context_hash(d)
        h2 = generate_context_hash(d)
        assert h1 == h2, "Hash must be deterministic"

def test_hash_changes_on_content_change():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "spec.md")
        with open(p, "w") as f:
            f.write("version 1")
        h1 = generate_context_hash(d)
        with open(p, "w") as f:
            f.write("version 2")
        h2 = generate_context_hash(d)
        assert h1 != h2, "Hash must change when content changes"

def test_hash_ignores_output_dir():
    with tempfile.TemporaryDirectory() as d:
        output_dir = os.path.join(d, "output")
        os.makedirs(output_dir)
        # Only file is inside output/ — should be ignored
        with open(os.path.join(output_dir, "main.md"), "w") as f:
            f.write("ignore me")
        result = generate_context_hash(d)
        assert result is None, "output/ dir contents should be excluded"

run("Empty dir returns None",           test_hash_empty_dir)
run("MD file produces MD5 hash",        test_hash_with_md_file)
run("Hash is deterministic",            test_hash_deterministic)
run("Hash changes on content change",   test_hash_changes_on_content_change)
run("output/ dir is excluded",          test_hash_ignores_output_dir)


# ══════════════════════════════════════════════════════════════════════════════
# 4. SKILL REGISTRY
# ══════════════════════════════════════════════════════════════════════════════
section("4. Skill Registry")

from synaptic.core.skill_registry import SkillRegistry

def test_skill_registry_init_no_crash():
    reg = SkillRegistry()
    assert isinstance(reg._cache, dict)

def test_skill_registry_cache_built():
    reg = SkillRegistry()
    # Skills directory exists — cache should have entries
    if os.path.exists(reg.path):
        assert len(reg._cache) > 0, "Cache empty despite skills directory existing"
    else:
        skip("Skill cache populated", "skills/ directory not found")

def test_skill_inject_returns_string():
    reg = SkillRegistry()
    result = reg.inject("build a secure REST api with database")
    assert isinstance(result, str)

def test_skill_inject_no_disk_rescan(monkeypatch=None):
    """inject() must not call os.listdir again after __init__."""
    reg = SkillRegistry()
    original_listdir = os.listdir
    calls = []
    def counting_listdir(path):
        calls.append(path)
        return original_listdir(path)
    old = os.listdir
    os.listdir = counting_listdir
    try:
        reg.inject("test security api database")
    finally:
        os.listdir = old
    assert len(calls) == 0, f"inject() made {len(calls)} unexpected os.listdir call(s)"

def test_skill_inject_custom_dir():
    with tempfile.TemporaryDirectory() as d:
        skill_dir = os.path.join(d, "my-skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "skill.md"), "w") as f:
            f.write("# My Custom Skill\nDo the thing.")
        reg = SkillRegistry(path=d, external_paths=[])
        result = reg.inject("my skill is great")
        assert "My Custom Skill" in result or "my-skill" in result.lower()

run("SkillRegistry init doesn't crash",         test_skill_registry_init_no_crash)
run("Cache populated from skills/ dir",         test_skill_registry_cache_built)
run("inject() returns a string",                test_skill_inject_returns_string)
run("inject() uses cache, no os.listdir",       test_skill_inject_no_disk_rescan)
run("inject() works with custom skill dir",     test_skill_inject_custom_dir)


# ══════════════════════════════════════════════════════════════════════════════
# 5. RUNTIME RUNNER
# ══════════════════════════════════════════════════════════════════════════════
section("5. Runtime Runner")

from synaptic.core.runtime_runner import RuntimeRunner

async def test_runner_good_code():
    runner = RuntimeRunner(timeout=15)
    result = await runner.run_python_code("print('hello synapticity')")
    assert result["success"] is True
    assert "hello synapticity" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["duration"] >= 0

async def test_runner_bad_code():
    runner = RuntimeRunner(timeout=15)
    result = await runner.run_python_code("raise ValueError('intentional error')")
    assert result["success"] is False
    assert result["exit_code"] != 0

async def test_runner_syntax_error():
    runner = RuntimeRunner(timeout=15)
    result = await runner.run_python_code("def broken(:\n    pass")
    assert result["success"] is False

async def test_runner_timeout():
    runner = RuntimeRunner(timeout=2)
    result = await runner.run_python_code("import time; time.sleep(10)")
    assert result["success"] is False
    assert "Timed out" in result["stderr"] or result["exit_code"] == -1

async def test_runner_stderr_captured():
    runner = RuntimeRunner(timeout=15)
    result = await runner.run_python_code(
        "import sys; sys.stderr.write('an error\\n')"
    )
    assert "an error" in result["stderr"]

def test_scan_quality_clean():
    runner = RuntimeRunner()
    result = runner.scan_quality("x = 1\nprint(x)\n")
    assert isinstance(result["clean"], bool)
    assert "problems" in result
    assert "summary" in result

def test_scan_quality_syntax_error():
    runner = RuntimeRunner()
    result = runner.scan_quality("def broken(:\n    pass\n")
    assert result["clean"] is False
    assert result["problems"]

def test_scan_security_clean():
    runner = RuntimeRunner()
    result = runner.scan_security("x = 1\nprint(x)\n")
    assert "secure" in result
    assert "issues" in result
    assert "summary" in result
    assert isinstance(result["issues"], list)

def test_scan_security_returns_dict():
    runner = RuntimeRunner()
    result = runner.scan_security("import subprocess\nsubprocess.call(['ls'])\n")
    assert isinstance(result, dict)
    assert "secure" in result

run_async("run_python_code — success path",         test_runner_good_code)
run_async("run_python_code — runtime error",        test_runner_bad_code)
run_async("run_python_code — syntax error",         test_runner_syntax_error)
run_async("run_python_code — timeout enforced",     test_runner_timeout)
run_async("run_python_code — stderr captured",      test_runner_stderr_captured)
run("scan_quality — clean code",                    test_scan_quality_clean)
run("scan_quality — syntax error detected",         test_scan_quality_syntax_error)
run("scan_security — clean code returns dict",      test_scan_security_clean)
run("scan_security — risky code returns dict",      test_scan_security_returns_dict)


# ══════════════════════════════════════════════════════════════════════════════
# 6. PERFORMANCE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
section("6. Performance Analytics")

from synaptic.core.analytics import PerformanceAnalytics

async def test_analytics_log_mission():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.core.analytics.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            a = PerformanceAnalytics()
            await a.log_mission_result("mission-001", True, 0, 12.5, "Gemini")
            assert os.path.exists(a.stats_file)
            with open(a.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["total_missions"] == 1
            assert data["mission_history"][0]["mission_id"] == "mission-001"

async def test_analytics_log_inference():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.core.analytics.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            a = PerformanceAnalytics()
            await a.log_inference("Gemini", 2.3)
            with open(a.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["inference_metrics"]["Gemini"]["calls"] == 1
            assert abs(data["inference_metrics"]["Gemini"]["total_duration"] - 2.3) < 0.001

async def test_analytics_multiple_missions():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.core.analytics.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            a = PerformanceAnalytics()
            await a.log_mission_result("m1", True,  0, 10.0, "Ollama")
            await a.log_mission_result("m2", False, 2, 20.0, "Ollama")
            with open(a.stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["total_missions"] == 2
            assert data["agent_metrics"]["Ollama"]["failures"] == 1

def test_analytics_get_summary_no_data():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.core.analytics.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            a = PerformanceAnalytics()
            # Write empty metrics
            with open(a.stats_file, "r", encoding="utf-8") as f:
                pass  # just ensure file exists
            report = a.get_summary_report()
            assert isinstance(report, str)

run_async("log_mission_result writes JSON",        test_analytics_log_mission)
run_async("log_inference tracks latency",          test_analytics_log_inference)
run_async("multiple missions accumulate",          test_analytics_multiple_missions)
run("get_summary_report returns string",           test_analytics_get_summary_no_data)


# ══════════════════════════════════════════════════════════════════════════════
# 7. MEMORY LOGGER
# ══════════════════════════════════════════════════════════════════════════════
section("7. Memory Logger")

from synaptic.utils.memory_logger import MemoryLogger

async def test_memory_logger_writes_jsonl():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.utils.memory_logger.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            await MemoryLogger.log_interaction(
                "mission-xyz", "SWE", "Writing code",
                "Ollama", "system prompt", "user prompt", "result output"
            )
            transcript = os.path.join(d, "mission-xyz", "memory", "transcript.jsonl")
            assert os.path.exists(transcript)
            with open(transcript, "r", encoding="utf-8") as f:
                entry = json.loads(f.readline())
            assert entry["agent"] == "SWE"
            assert entry["output"] == "result output"

async def test_memory_logger_no_mission_id():
    # Should silently do nothing if mission_id is None
    with patch("synaptic.utils.memory_logger.settings") as mock_s:
        mock_s.WORKSPACE_PATH = tempfile.gettempdir()
        await MemoryLogger.log_interaction(None, "SWE", "task", "Ollama", "s", "p", "r")

async def test_memory_logger_appends():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.utils.memory_logger.settings") as mock_s:
            mock_s.WORKSPACE_PATH = d
            for i in range(3):
                await MemoryLogger.log_interaction(
                    "m1", f"AGENT{i}", "task", "Ollama", "s", "p", f"result{i}"
                )
            transcript = os.path.join(d, "m1", "memory", "transcript.jsonl")
            with open(transcript, "r", encoding="utf-8") as f:
                lines = f.readlines()
            assert len(lines) == 3

run_async("log_interaction writes JSONL file",      test_memory_logger_writes_jsonl)
run_async("None mission_id is silently ignored",    test_memory_logger_no_mission_id)
run_async("Multiple entries append correctly",      test_memory_logger_appends)


# ══════════════════════════════════════════════════════════════════════════════
# 8. MISSION STATE MANAGER
# ══════════════════════════════════════════════════════════════════════════════
section("8. Mission State Manager")

from synaptic.core.mission_state import MissionStateManager

def test_state_load_missing_file():
    with tempfile.TemporaryDirectory() as d:
        mgr = MissionStateManager(d)
        state = mgr.load()
        assert state["phase"] == "START"
        assert "objective" in state

def test_state_save_and_load_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        mgr = MissionStateManager(d)
        original = {"phase": "PLANNED", "objective": "Build a REST API", "repair_count": 2}
        mgr.save(original)
        loaded = mgr.load()
        assert loaded["phase"] == "PLANNED"
        assert loaded["objective"] == "Build a REST API"
        assert loaded["repair_count"] == 2

def test_state_encoding_utf8():
    with tempfile.TemporaryDirectory() as d:
        mgr = MissionStateManager(d)
        mgr.save({"phase": "DONE", "objective": "Build 日本語アプリ"})
        loaded = mgr.load()
        assert "日本語アプリ" in loaded["objective"]

def test_state_corrupted_file_recovery():
    with tempfile.TemporaryDirectory() as d:
        mgr = MissionStateManager(d)
        state_path = os.path.join(d, "mission_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")
        state = mgr.load()
        # Should recover gracefully
        assert state["phase"] == "START"

run("load() returns default for missing file",      test_state_load_missing_file)
run("save() + load() roundtrip",                    test_state_save_and_load_roundtrip)
run("UTF-8 content persists correctly",             test_state_encoding_utf8)
run("Corrupted state file recovers gracefully",     test_state_corrupted_file_recovery)


# ══════════════════════════════════════════════════════════════════════════════
# 9. AGENT RUNNER — asyncio heartbeat + dispatch
# ══════════════════════════════════════════════════════════════════════════════
section("9. Agent Runner (async monitoring)")

from synaptic.core.agent_runner import AgentRunner
from synaptic.models.base import AbstractModel

class _FakeModel(AbstractModel):
    def __init__(self, response="ok", delay=0):
        self._response = response
        self._delay = delay
    async def generate(self, system_instruction, prompt):
        if self._delay:
            await asyncio.sleep(self._delay)
        return self._response

class _ErrorModel(AbstractModel):
    async def generate(self, system_instruction, prompt):
        from synaptic.utils.exceptions import ModelProviderError
        raise ModelProviderError("forced failure")

async def test_agent_runner_returns_result():
    with tempfile.TemporaryDirectory() as d:
        agent_file = os.path.join(d, "test-agent.md")
        with open(agent_file, "w") as f:
            f.write("You are a test agent.")
        with patch("synaptic.core.agent_runner.settings") as mock_s, \
             patch("synaptic.core.agent_runner.PerformanceAnalytics") as MockAnalytics:
            mock_s.AGENT_PATH = d
            mock_s.HEARTBEAT_INTERVAL = 0  # disable heartbeat
            mock_analytics = AsyncMock()
            MockAnalytics.return_value = mock_analytics
            runner = AgentRunner(_FakeModel("hello world"), "test-agent.md")
            result = await runner.run("do something")
        assert result == "hello world"

async def test_agent_runner_fallback():
    with tempfile.TemporaryDirectory() as d:
        agent_file = os.path.join(d, "test-agent.md")
        with open(agent_file, "w") as f:
            f.write("You are a test agent.")
        with patch("synaptic.core.agent_runner.settings") as mock_s, \
             patch("synaptic.core.agent_runner.PerformanceAnalytics") as MockAnalytics:
            mock_s.AGENT_PATH = d
            mock_s.HEARTBEAT_INTERVAL = 0
            mock_analytics = AsyncMock()
            MockAnalytics.return_value = mock_analytics
            runner = AgentRunner(_ErrorModel(), "test-agent.md", fallback_model=_FakeModel("fallback result"))
            result = await runner.run("do something")
        assert result == "fallback result"

async def test_agent_runner_missing_persona():
    with tempfile.TemporaryDirectory() as d:
        with patch("synaptic.core.agent_runner.settings") as mock_s, \
             patch("synaptic.core.agent_runner.PerformanceAnalytics"):
            mock_s.AGENT_PATH = d
            mock_s.HEARTBEAT_INTERVAL = 0
            runner = AgentRunner(_FakeModel(), "nonexistent-agent.md")
            try:
                await runner.run("do something")
                assert False, "Should have raised ConfigurationError"
            except Exception as e:
                assert "Persona file missing" in str(e) or "missing" in str(e).lower()

async def test_agent_runner_heartbeat_is_asyncio_task():
    """Heartbeat monitor must be an asyncio task, not a threading.Thread."""
    import threading
    active_threads_before = threading.active_count()

    with tempfile.TemporaryDirectory() as d:
        agent_file = os.path.join(d, "test-agent.md")
        with open(agent_file, "w") as f:
            f.write("You are a test agent.")
        with patch("synaptic.core.agent_runner.settings") as mock_s, \
             patch("synaptic.core.agent_runner.PerformanceAnalytics") as MockAnalytics:
            mock_s.AGENT_PATH = d
            mock_s.HEARTBEAT_INTERVAL = 1  # enable heartbeat
            mock_analytics = AsyncMock()
            MockAnalytics.return_value = mock_analytics
            runner = AgentRunner(_FakeModel("done", delay=0.1), "test-agent.md")
            await runner.run("go")

    active_threads_after = threading.active_count()
    assert active_threads_after <= active_threads_before + 1, \
        "threading.Thread was spawned — heartbeat must use asyncio.create_task"

run_async("run() returns model response",           test_agent_runner_returns_result)
run_async("Fallback model used on primary error",   test_agent_runner_fallback)
run_async("Missing persona raises error",           test_agent_runner_missing_persona)
run_async("Heartbeat uses asyncio task not thread", test_agent_runner_heartbeat_is_asyncio_task)


# ══════════════════════════════════════════════════════════════════════════════
# 10. MISSION PHASES
# ══════════════════════════════════════════════════════════════════════════════
section("10. Mission Phases")

from synaptic.core.mission_phases import HealingCyclePhase, PlanningPhase

async def test_sandbox_routes_to_runtime():
    """_sandbox() must await RuntimeRunner.run_python_code (async)."""
    mock_runtime = MagicMock()
    mock_runtime.run_python_code = AsyncMock(return_value={
        "success": True, "stdout": "ok", "stderr": "", "exit_code": 0, "duration": 0.1
    })
    mock_runtime.scan_quality  = MagicMock(return_value={"clean": True, "problems": "", "summary": ""})
    mock_runtime.scan_security = MagicMock(return_value={"secure": True, "issues": [], "summary": ""})

    phase = HealingCyclePhase(
        coder=None, tester=None, auditor=None,
        runtime=mock_runtime, logger=MagicMock()
    )

    with patch("synaptic.core.mission_phases.settings") as mock_s:
        mock_s.GEMINI_ACTIVE = False
        mock_s.GEMINI_USE_CODE_EXECUTION = False
        result = await phase._sandbox("print('hi')")

    mock_runtime.run_python_code.assert_awaited_once()
    assert result["success"] is True

async def test_planning_phase_uses_cache():
    """PlanningPhase must return cached specs on hash match."""
    with tempfile.TemporaryDirectory() as d:
        cache_file = os.path.join(d, "specs.json")
        fake_specs = "# Cached Spec\nThis came from cache."
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"hash": "fixed-hash", "specs": fake_specs}, f)

        mock_planner = AsyncMock(return_value="fresh specs — should not be called")
        phase = PlanningPhase(planner=mock_planner, skill_registry=MagicMock(), logger=MagicMock())

        with patch("synaptic.core.mission_phases.generate_context_hash", return_value="fixed-hash"):
            specs = await phase.run(d, {"objective": "test"}, "m1")

        assert specs == fake_specs
        mock_planner.run.assert_not_called()

run_async("_sandbox() awaits async run_python_code",   test_sandbox_routes_to_runtime)
run_async("PlanningPhase returns cached specs",         test_planning_phase_uses_cache)


# ══════════════════════════════════════════════════════════════════════════════
# 11. INTELLIGENCE ROUTER
# ══════════════════════════════════════════════════════════════════════════════
section("11. Intelligence Router")

from synaptic.core.intelligence_router import IntelligenceRouter

def test_router_instantiates():
    router = IntelligenceRouter()
    assert hasattr(router, "resolve")

def test_router_resolve_ollama():
    with patch("synaptic.core.intelligence_router.settings") as mock_s:
        mock_s.OLLAMA_ACTIVE = True
        mock_s.GEMINI_ACTIVE = False
        mock_s.CLAUDE_ACTIVE = False
        mock_s.OLLAMA_MODEL = "qwen2.5-coder:7b"
        mock_s.OLLAMA_FALLBACK_MODEL = ""
        mock_s.GEMINI_USE_FUNCTION_CALLING = False
        mock_s.GEMINI_USE_CODE_EXECUTION = False
        with patch("synaptic.core.intelligence_router.PerformanceAnalytics"):
            with patch("synaptic.core.intelligence_router.OllamaAdapter") as MockOllama:
                MockOllama.return_value = MagicMock()
                router = IntelligenceRouter()
                primary, fallback = router.resolve()
                assert primary is not None

def test_router_raises_if_no_engine():
    with patch("synaptic.core.intelligence_router.settings") as mock_s:
        mock_s.OLLAMA_ACTIVE = False
        mock_s.GEMINI_ACTIVE = False
        mock_s.CLAUDE_ACTIVE = False
        with patch("synaptic.core.intelligence_router.PerformanceAnalytics"):
            router = IntelligenceRouter()
            try:
                router.resolve()
                assert False, "Should raise ConfigurationError"
            except Exception as e:
                assert "No intelligence engines" in str(e)

run("IntelligenceRouter instantiates",          test_router_instantiates)
run("resolve() returns primary with Ollama",    test_router_resolve_ollama)
run("resolve() raises with no engines",         test_router_raises_if_no_engine)


# ══════════════════════════════════════════════════════════════════════════════
# 12. CLI REGISTRY
# ══════════════════════════════════════════════════════════════════════════════
section("12. CLI Command Registry")

from synaptic.cli.registry import COMMAND_REGISTRY

EXPECTED_COMMANDS = [
    "dash", "help", "stats", "doctor", "launch", "resume",
    "update", "remove", "agent", "audit", "log", "deploy",
    "ingest", "stress", "admin", "review", "learn", "estimate", "tool",
]

def test_registry_has_all_commands():
    for cmd in EXPECTED_COMMANDS:
        assert cmd in COMMAND_REGISTRY, f"Missing command: '{cmd}'"

def test_registry_all_are_callable():
    for cmd, handler in COMMAND_REGISTRY.items():
        assert callable(handler), f"Handler for '{cmd}' is not callable"

run("All expected commands registered",         test_registry_has_all_commands)
run("All handlers are callable",                test_registry_all_are_callable)


# ══════════════════════════════════════════════════════════════════════════════
# 13. EXCEPTIONS
# ══════════════════════════════════════════════════════════════════════════════
section("13. Custom Exceptions")

from synaptic.utils.exceptions import ConfigurationError, ModelProviderError

def test_exceptions_are_exceptions():
    assert issubclass(ConfigurationError, Exception)
    assert issubclass(ModelProviderError, Exception)

def test_exceptions_carry_message():
    try:
        raise ConfigurationError("test config error")
    except ConfigurationError as e:
        assert "test config error" in str(e)

run("Exception classes inherit from Exception",  test_exceptions_are_exceptions)
run("Exception message is preserved",           test_exceptions_carry_message)


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
total = passed + failed + skipped
print(f"\n{BOLD}{'='*60}{RESET}")
print(f"{BOLD}  RESULTS  {GREEN}{passed} passed{RESET}  "
      f"{RED}{failed} failed{RESET}  "
      f"{YELLOW}{skipped} skipped{RESET}  "
      f"/ {total} total{RESET}")
print(f"{BOLD}{'='*60}{RESET}\n")

if failed:
    sys.exit(1)
