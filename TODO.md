# Synapticity — Master TODO
# Single source of truth. tasks.txt retired. Update this file for every change.
# Format: [x] Done  [ ] Pending  [~] In Progress

---

## ACTIVE — Pending Items

### Async & Performance (Phase 27)
- [x] Replace `subprocess.run` in `HealingCyclePhase` with `asyncio.create_subprocess_exec` (`runtime_runner.py` → `async run_python_code`)
- [x] Offload blocking JSON I/O in `PerformanceAnalytics` and `MemoryLogger` to `asyncio.to_thread()`
- [x] Replace `threading.Thread` heartbeat monitor in `AgentRunner` with `asyncio.create_task`
- [x] Rebuild `runtime_runner.py` — complete rewrite with correct async subprocess, bandit, ruff/pylint

### Code Quality (Phase 28)
- [x] Remove double directory scanning in `SkillRegistry.inject()` — now iterates `self._cache.keys()`
- [x] Add `encoding='utf-8'` to all `json.dump` / `json.load` calls across the framework

### Rate-Limit Reliability (Phase 26)
- [x] Make `SLEEP_BUFFER` tier-aware: free-tier Gemini keys need longer buffers than paid-tier

### Estimation Engine (Phase 29)
- [x] Add AI-enhanced estimation: LLM refines PERT task breakdowns from document context
- [ ] Support custom task templates via external skill configuration

### Orchestration & Scale (Phase 21)
- [ ] Persistent Resource Cache: semantic index of common library patterns → reduce PM/SWE reasoning overhead
- [ ] Multi-Modal Review: Ollama vision models for automated UI/UX auditing of frontend projects
- [ ] Parallel Multi-Mission: run multiple `MissionEngine` instances in separate worker processes
- [ ] Dynamic System Prompting: agents adjust their own identity based on successful Reflection Cycles

### Local Hardware (Phase 23)
- [ ] Faster agent startup — sub-second boot-up for local inference
- [ ] DirectML / ROCm support for AMD Radeon 780M (integrated APU)
- [ ] High-quantization GGUF tuning for high-density local reasoning

### Long-Term Memory (Phase 24)
- [ ] External sync with Logseq / Obsidian for personal knowledge graph integration
- [ ] Formalize 256K-token Context Buffer as a "Working Set" for high-speed retrieval

### Self-Learning — Idle Mode (Phase 25)
- [ ] Local fine-tuning from failed mission transcripts using Unsloth
- [x] Idle Learning Mode: auto-retry failed tasks when machine is idle
- [ ] Success-Based Routing: route missions to agents with best historical success rates
- [ ] Human Feedback Loop: thumb-up / thumb-down on generated projects to guide future learning
- [ ] System Cleanup: auto-remove inefficient logic paths based on performance analytics

### Gemini Agentic Intelligence (Phase 31 — follow-ons)
- [x] Upgrade `GEMINI_MODEL` default to `gemini-2.5-flash` once key pool is tested against new quotas
- [x] Wire MCP `ClientSession` into `GeminiToolAdapter` config (full MCP → Gemini roundtrip)
- [x] `GeminiCodeRunner.scan_quality()` integrated into `HealingCyclePhase` quality step

### Future Backlog
- [x] Unit test suite: `test_suite.py` — 55 tests, 13 sections, 0 external API dependencies
- [ ] Web UI / TUI dashboard: `rich` + `textual` or lightweight FastAPI status page
- [ ] Plugin system: drop `synaptic/plugins/<name>.py` and auto-discover at startup
- [ ] Voice-to-Mission: hardware trigger integration for mission launching

---

## RECENTLY COMPLETED

### Phase 27–28 — Async Hardening & Code Quality
- [x] `runtime_runner.py` full rewrite — `async run_python_code` via `asyncio.create_subprocess_exec`, correct `scan_security` (bandit) and `scan_quality` (ruff/pylint)
- [x] `mission_phases._sandbox()` updated to `await self._runtime.run_python_code(code)`
- [x] `PerformanceAnalytics.log_mission_result` and `log_inference` → async, blocking I/O offloaded via `asyncio.to_thread()`
- [x] `MemoryLogger.log_interaction` → async static, I/O via `asyncio.to_thread()`
- [x] `MissionEngine._log_mission_performance` → async, call sites awaited
- [x] `AgentRunner` heartbeat: `threading.Thread` + `threading.Event` replaced with `asyncio.create_task` + `asyncio.Event`; `_run_progress_monitor` is now an async coroutine
- [x] `SkillRegistry.inject()` double disk scan removed — uses `self._cache.keys()` instead of `os.listdir()`
- [x] `encoding='utf-8'` added to all `open()` / `json.dump` / `json.load` calls in `analytics.py`, `memory_logger.py`, `runtime_runner.py`

### Phase 31 — Gemini Agentic Intelligence (Function Calling + Code Execution)
- [x] `_api_call()` protected helper extracted into `GeminiAdapter` (DRY rate-limit retry)
- [x] `GeminiToolAdapter` (`synaptic/models/gemini_tool.py`) — multi-turn agentic loop, parallel `asyncio.gather()` dispatch, function_call `id` tracking
- [x] `SynapticToolDispatcher` (`synaptic/core/tool_dispatcher.py`) — skills + organs as typed Gemini function declarations
- [x] `GeminiCodeRunner` (`synaptic/core/gemini_code_runner.py`) — Google's server-side Python sandbox, `RuntimeRunner`-compatible return format
- [x] `SynapticMCPServer` (`synaptic/organs/mcp_server.py`) — FastMCP server: `search_memory`, `store_reflection`, `get_vision_report`, `send_report`, `organ_health_check`
- [x] `./sync tool <tool_name> [args]` CLI command registered (`handle_tool`)
- [x] `GEMINI_USE_FUNCTION_CALLING`, `GEMINI_USE_CODE_EXECUTION`, `MAX_TOOL_ROUNDS` added to `config.py`
- [x] `IntelligenceRouter` auto-upgrades to `GeminiToolAdapter` when agentic flags enabled
- [x] `HealingCyclePhase._run_sandbox` routes to `GeminiCodeRunner` with local fallback
- [x] `mcp` added to `requirements.txt`

### Phase 31 — Bug Fixes (code review pass)
- [x] **CRITICAL** `mission_phases.py`: `asyncio.get_event_loop().run_until_complete()` inside async → made `_run_sandbox` async, proper `await`
- [x] **HIGH** `SynapticOrganInterface`: efferent alias expanded to independent entries so `ResendSynapse` failure no longer blocks `TwilioReflex`
- [x] **HIGH** `GlobalMetabolicLock.acquire_key_slot()`: index now advances to `(candidate + 1) % num_keys` preventing two callers claiming the same key
- [x] **MEDIUM** `PostHogSensoryFeedback._query_events()`: `after` param fixed to ISO 8601 datetime (was invalid `-24h` string)
- [x] **MEDIUM** `httpx.AsyncClient` resource leak: `aclose()` added to `SentryNociceptor`, `PostHogSensoryFeedback`, `ResendSynapse`, `TwilioReflex` and `SynapticOrganInterface`
- [x] **LOW** `TwilioReflex`: auth header cached at `__init__` instead of rebuilt on every API call

### Phase 30 — Production Synapse Layer (SaaS Organs)
- [x] `synaptic/organs/` package: `GlobalMetabolicLock`, `SupabaseMemoryProvider`, `SentryNociceptor`, `PostHogSensoryFeedback`, `ResendSynapse`, `TwilioReflex`, `SynapticOrganInterface`
- [x] Supabase migration `001_neural_firings.sql`: pgvector, IVFFlat ANN index, RLS policies, RPC functions
- [x] Phase 26 settings block in `config.py` (all env vars for all 5 SaaS services)
- [x] `upstash-redis`, `supabase`, `posthog` added to `requirements.txt`

### Phase 29 — Professional Estimation Engine
- [x] `DocumentParser` (PDF/DOCX/TXT), `EstimationEngine` (PERT), estimation skill + agent persona
- [x] `./sync estimate <document>` CLI command; task-level PERT breakdown in reports
- [x] addyosmani/agent-skills fetched into `skills-external/` (20 skills)

### Phases 26–28 — Hardening
- [x] `GeminiAdapter`: `asyncio.Lock()`, per-key cooldowns, exponential backoff
- [x] `httpx.AsyncClient` reuse in `ClaudeAdapter` and `OllamaAdapter`
- [x] Lazy-load adapters in `IntelligenceRouter`
- [x] `indent=2` in `MissionStateManager.save()`

### Phases 1–25 — Foundation through Self-Learning
- [x] Full SDLC orchestration: 4-phase `MissionEngine` (Plan → Dev → Heal → Finalize)
- [x] 6 agent personas, 33 local skills + external skill loading
- [x] Multi-key Gemini pool, Ollama local inference, Claude adapter
- [x] `IntelligenceRouter` with reliability rotation (< 40% → promote fallback)
- [x] Parallel QA + Security verification via `asyncio.gather()`
- [x] `SkillRegistry` hot-reload, keyword injection, external override
- [x] `MemoryLogger` JSONL transcripts, `PerformanceAnalytics` scorecards
- [x] `MissionStateManager`, `MissionLogger`, `MissionWorkspace` SOLID split
- [x] `SelfLearningEngine` + `ReflectorAgent` for post-mission lessons
- [x] `ProjectReviewEngine` (3-agent external review + `FILE_PATCH` write-back)
- [x] GitHub `GitDeployer` + full CI/CD pipeline synthesis
- [x] `./sync` CLI: launch, resume, update, remove, agent, audit, log, deploy, ingest, review, learn, estimate, stats, doctor, tool
