# Synaptic Agentic Framework (v3.0)

> A Staff-Engineer level autonomous Software Development Life Cycle (SDLC) system designed for high-IQ software production. Synapticity leverages a hybrid Local (Ollama) and Cloud (Gemini) intelligence model to ensure zero-cost, private, and resilient engineering.

---

## [STRATEGY] System Philosophy & Best Practices

Synapticity is not just a code generator; it is a **State Machine** that mimics the rigorous processes of a high-functioning engineering team. To get the best results in practice, adhere to the following operational standards:

### 1. The Human-In-The-Loop (HITL) Principle
While the framework acts autonomously, you are the **Principal Architect**. 
- **Observe the Audits:** Do not blindly approve code hand-offs. Use the `./sync audit <id>` command to review the exact architectural path the agents took.
- **Enforce Checkpoints:** The system naturally stops at critical milestones (Planning, Implementation, Healing). Use these pauses to read `MISSION_LOG.md` before authorizing the next phase via terminal input.

### 2. Iterative Spec Engineering
Agents perform best with tight, scoped objectives. 
- **Start Small:** Use `./sync launch <id> "Objective"` for foundational scaffolding.
- **Pivot Gracefully:** If you realize the AI is drifting, use `./sync update <id> "New Objective"` to wipe the corrupted state and force the Product Manager persona to re-draft specifications without breaking the SDLC loop.

### 3. Surgical Agent Dispatch
You do not always need to run a full SDLC loop. 
- Use the **Solo Agent** command (`./sync agent <id> <persona> "task"`) to dispatch specific agents to your workspace. 
- Example: If the documentation is lacking, run `./sync agent my-app writer "Expand the API endpoints documentation"` instead of regenerating the entire project.

---

## [LAUNCH] Quick Start Guide

### 1. Core Installation
Install the professional dependency stack required for telemetry, security scanning, and API adaptation:

```bash
pip install google-genai requests python-dotenv rich pydantic-settings cryptography bandit pytest
```

### 2. Environment Configuration
1. Install [Ollama](https://ollama.com/) locally and ensure it is running (`http://localhost:11434`). This is the primary intelligence engine.
2. Copy `.env.example` to `.env`.
3. Add your Gemini API keys for the Cloud Fallback network.

### 3. Health Verification
Before launching missions, always verify that your environment, intelligence networks, and dependencies are cleanly connected:
```bash
./sync doctor
```

---

## [CLI] Command Center Operations

Manage your workspaces through the `main.py` CLI interface via the `./sync` alias.

| Command | Usage Example | Description |
| :--- | :--- | :--- |
| **dash** | `./sync dash` | View all active mission titles, statuses, and live verdicts. |
| **launch** | `./sync launch auth-svc "Build a JWT API"`| Initiates a new SDLC loop from scratch. |
| **resume** | `./sync resume auth-svc` | Continues a paused or checkpointed mission. |
| **update** | `./sync update auth-svc "Add OAuth2 support"` | Overrides the current objective and re-triggers the planning lifecycle. |
| **audit** | `./sync audit auth-svc` | Displays the historical task list and predicts the upcoming agent queues. |
| **agent** | `./sync agent auth-svc swe "Refactor utils.py"`| Sends a single agent directly into the workspace to perform a surgical task. |
| **remove** | `./sync remove auth-svc` | Safely and permanently purges a mission directory from the workspace. |
| **deploy** | `./sync deploy auth-svc` | Utilizes GitHub APIs to create a pristine repository and autonomously push pipelines. |
| **ingest** | `./sync ingest agent http... name` | Resolves external `skill` or `agent` payload playbooks natively into the core engine. |

---

## [SEC] Architecture & Security

Synapticity enforces a **Zero-Defect Security Model**:
1. **Sandboxed Runtimes:** Code synthesized by the Software Engineer persona is executed inside a simulated runtime.
2. **Bandit Scans:** Static vulnerability analysis is run passively against all emitted code.
3. **Healing Cycles (Max 3):** If code fails execution or fails the security scan, the `TESTER` and `ONCALL-ENGINEER` personas instruct the `SOFTWARE-ENGINEER` how to apply targeted remediation patches automatically.

> **Deep Dive:** For full architectural breakdowns, state-machine mechanics, and data flow diagrams, refer to the [architecture_map.md](architecture_map.md).

---
*Developed for autonomous excellence. Build fearlessly.*
