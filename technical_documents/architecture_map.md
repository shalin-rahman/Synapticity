# Synapticity 3.2: Comprehensive Architecture & Method Inventory

This document serves as the definitive technical reference for the Synapticity autonomous engineering platform. It documents every class, method, and operational workflow that drives the framework's intelligence and lifecycle.

---

## 1. How a Mission Runs (Operational Workflows)

Synapticity is fundamentally a **State-Driven Workflow Engine**. It transitions through five discrete phases, governed by strict verification gates.

### Workflow A: The Standard Mission (launch/resume)
1.  **Bootstrap**: `main.py` uses `config.py` to load environment variables and routes the user command to `registry.py`.
2.  **Initialization**: `MissionStateManager` loads or creates `state.json`. `OllamaAdapter` starts its non-blocking "Warp-Speed" pre-warming thread.
3.  **Phase 1: Planning**: 
    - `MissionEngine` dispatches the **Product Manager** agent.
    - `SkillRegistry.inject()` scans the goal for keywords (e.g., "fastapi") and provides technical playbooks.
    - Result: `specs.json` (cached via `hashing.py`) containing the architectural blueprint.
4.  **Phase 2: Development**:
    - The **Software Engineer** agent receives the blueprint.
    - It synthesizes source code.
    - `MissionWorkspace.commit_code()` performs an atomic write to the mission folder.
5.  **Phase 3: The Healing Cycle (Parallel Verification)**:
    - `RuntimeRunner` executes the code in a sandbox (Bare-metal or Docker).
    - `MissionEngine` dispatches **QA** and **Security Auditor** agents **simultaneously** using `concurrent.futures`.
    - If errors are detected, the **Software Engineer** applies iterative patches until a dual-PASS verdict is reached.
6.  **Phase 4: Finalization**:
    - **Technical Writer** generates markdown documentation.
    - **DevOps Engineer** synthesizes GitHub Action YAML pipelines.
    - `GitDeployer` optionally pushes the verified code to a remote repository.
7.  **Phase 5: Post-Mortem Reflection**:
    - `ReflectionEngine` analyzes mission logs to synthesize and persist new engineering skills.

---

## 2. Core Library Inventory (`synaptic/core/`)

| File | Class / Component | Primary Methods & Functionality Details |
| :--- | :--- | :--- |
| `mission_engine.py` | `MissionEngine` | `run(mission_id, objective)`: Orchestrates the 4-phase SDLC. Manages state loading and finalization.<br>`_resolve_optimal_routing()`: Dynamically selects the best primary/fallback models based on health.<br>`_finalize()`: Triggers doc/CI-CD generation and workspace commits. |
| `agent_runner.py` | `AgentRunner` | `run(prompt, context, task)`: The primary worker entry point. Loads persona files and handles AI dispatch.<br>`_dispatch_with_monitoring()`: Private handle for `rich.console` progress indicators and failover logic.<br>`_run_progress_monitor()`: Background thread providing "heartbeat" status updates during long calls. |
| `mission_phases.py` | `PlanningPhase` | `run()`: Translates goals into specs. Implements context-hashing to skip redundant planning (Cache-First). |
| | `HealingCyclePhase` | `run()`: Manages the iterative retry-loop. Coordinates parallel QA/Sec dispatches and Patching. |
| `project_review_engine.py` | `ProjectReviewEngine` | `review(project_path, goal, mission_id)`: Multi-agent audit of external local codebases. Supports `FILE_PATCH` write-back.<br>`_apply_patches()`: Regex-based parser that updates physical files on disk based on agent suggestions. |
| `skill_registry.py` | `SkillRegistry` | `inject(target_str)`: Analyzes tasks for keywords and creates an augmented system prompt including best-practice playbooks.<br>`_check_hot_reload()`: Monitors disk files to ensure updated skills are used without framework restart. |
| `runtime_runner.py` | `RuntimeRunner` | `run_python_code(code)`: Safely executes AI code in a temp sandbox. Captures timing, stdout, and stderr.<br>`scan_security(code)`: Integrates **Bandit** for static analysis of vulnerabilities inside generated content. |
| `self_learning.py` | `ReflectionEngine` | `analyze(mission_id)`: Post-mission log synthesizer. Transforms mission history into permanent markdown playbooks in `autonomous-lessons/`. |
| `mission_state.py` | `MissionStateManager` | `load()` / `save()`: High-reliability JSON I/O for `state.json` ensuring persistence across framework restarts. |
| `mission_workspace.py` | `MissionWorkspace` | `commit_code()` / `commit_docs()`: Standardized handlers for isolating mission output from framework source. |
| `analytics.py` | `PerformanceAnalytics` | `log_inference()`: Tracks provider latency and token density.<br>`log_mission_result()`: Aggregates success/fail metrics to drive **Autonomous Role Rotation**. |
| `agent_dispatcher.py` | `resolve_runner` | A functional router that maps string titles (e.g., "swe", "qa") to the correct class instance in `MissionEngine`. |
| `mission_gate.py` | `ApprovalGate` | `request(message, phase)`: Implements "Human-In-The-Loop" breakpoints if `INTERACTIVE_MODE` is active. |

---

## 3. Intelligence Layer (`synaptic/models/`)

| File | Class | Key Responsibilities & Logic |
| :--- | :--- | :--- |
| `base.py` | `AbstractModel` | The SOLID interface (ABC) defining the mandatory `generate()` contract. |
| `ollama.py` | `OllamaAdapter` | **Zero-Latency local driver**. Implements `-1 keep_alive` for infinite residency and background `pre_warm()` on init. |
| `gemini.py` | `GeminiAdapter` | **Cloud fallback engine**. Manages a rotation pool of up to 10 API keys with per-key rate limiting. |
| `claude.py` | `ClaudeAdapter` | **High-Reasoning driver**. Targets Anthropic's Sonnet/Opus models for hyper-complex project audits. |

---

## 4. Technical Utilities (`synaptic/utils/`)

| File | Component | Detailed Functionality |
| :--- | :--- | :--- |
| `doctor.py` | `SynapticDoctor` | `run_full_service()`: Comprehensive health audit (Keys, Connectivity, Models). Triggers `heal()` to auto-fix missing components. |
| `git_deployer.py` | `GitDeployer` | `deploy(path, mission_id)`: Orchestrates `git init`, GitHub Repository creation (REST API), and initial code push. |
| `project_indexer.py` | `ProjectIndexer` | `build_context()`: Recursive crawler that builds a semantic "Map" of any external project for agent review. |
| `memory_logger.py` | `MemoryLogger` | `log_interaction()`: Low-level JSONL append logic for lossless capture of all framework input/output history. |
| `formatting.py` | (Utility) | `strip_markdown_backticks()`: Turbo-remediation logic to extract raw source code from LLM stylistic containers. |
| `logger.py` | (Global) | `synaptic_log`: A resilient, thread-safe logger targeting `logs/synaptic.log` with auto-console fallback. |

---

## 5. Command Hub (`synaptic/cli/`)

| File | Sub-System | Purpose |
| :--- | :--- | :--- |
| `registry.py` | `COMMAND_REGISTRY` | The OCP (Open-Closed Principle) extension point. Maps CLI strings to specialized action handlers. |
| `ui.py` | (Rich UI) | `show_dashboard()`: Provides the real-time mission monitor table.<br>`show_help()`: Dynamically generates the command help panel. |
| `handlers/` | (Command Logic) | De-coupled functions (e.g., `handle_launch`, `handle_learn`) that isolate CLI logic from internal engine orchestration. |

---

## 6. Guardrails & Performance Summary

1.  **Concurrency**: Parallel model pre-warming and dual-agent verification minimize idling.
2.  **Safety**: Static analysis (Bandit) and isolated sandboxing prevent host system exposure.
3.  **Persistence**: Every mission is traceable via `state.json` and searchable through `MISSION_LOG.md`.
4.  **Resilience**: Auto-failover from Local (Ollama) to Cloud (Gemini) ensures mission continuity during hardware overloads.
