# Synapticity Framework (v3.3)

Synapticity is an autonomous software development platform engineered for precision-grade project synthesis. It operates as a digital "Smart Factory," coordinating a specialized hierarchy of AI agents to manage the entire lifecycle—from high-level planning and secure implementation to autonomous CI/CD deployment.

By combining low-latency local processing (via Ollama) with a high-capacity cloud fallback (via Gemini/Claude), Synapticity provides the most resilient and secure environment for autonomous software engineering.

---

## Core Philosophy: The Smart Factory

Instead of functioning like a generic chat assistant, Synapticity follows a structured, verified engineering workflow based on industry best practices:

### 1. Verification-First Culture

We prioritize quality through a strict "Verification Gate." A code artifact isn't considered complete until it passes both functional testing and security checks. If it finds a defect, the system automatically runs a Healing Cycle to apply patches without needing you to step in.

### 2. Smart Thinking Playbooks

Unlike basic LLM wrappers, Synapticity injects specialized **Engineering Playbooks** (Skills) directly into the agents' context. These playbooks provide world-class standards for SOLID design, OWASP security, and Agile product management.

### 3. Warp-Speed Local Intelligence

Optimized for the "Free-Forever" setup, the framework includes hardware-level optimizations for Ollama, including non-blocking model pre-warming and infinite VRAM residency, delivering a "Claude-like" experience at zero cost.

### 4. Surgical Custom Directives

Take granular control of your team by injecting role-specific instructions directly into the objective.

- **Precision Steering**: Use tags like `[SWE: use FastAPI]` or `[QA: focus on performance]` to override default behaviors.
- **Global Persistence**: Instructions are stored in the mission state and prioritized during every healing and verification cycle.
- **Supported Roles**: `[PM: ...]`, `[SWE: ...]`, `[QA: ...]`, `[SEC: ...]`, `[DOC: ...]`.

---

## Getting Started

### 1. Deployment

Install the core framework and verification dependencies:

```bash
pip install google-genai requests python-dotenv rich pydantic-settings cryptography bandit pytest
```

### 2. Configure Your Engine

1. **Local LLM:** Install [Ollama](https://ollama.com/). The framework is pre-configured to target `gemma4:latest` (or your chosen model) via `http://localhost:11434`.
2. **Environment:** Copy `.env.example` to `.env`.
3. **Hardware Lock:** Ensure you have assigned enough VRAM to your local model for the best reasoning performance.

### 3. System Health Check

Run the internal diagnostic engine to verify connectivity:

```bash
./sync doctor
```

---

## Command Reference

| Command          | Usage Example                                            | Description                                                            |
| :--------------- | :------------------------------------------------------- | :--------------------------------------------------------------------- |
| **launch** | `./sync launch auth-svc "Build a JWT API"`             | Start a new 4-phase development mission.                               |
| **resume** | `./sync resume auth-svc`                               | Continue a paused mission from the last checkpoint.                    |
| **update** | `./sync update auth-svc "Add OAuth2 support"`          | Pivot an existing mission and re-plan specifications.                  |
| **agent**  | `./sync agent auth-svc swe "Refactor utils.py"`        | Dispatch a solo agent for a targeted tactical task.                    |
| **review** | `./sync review bug-fix "security audit" C:/my-project` | Run a 3-agent audit and patch loop on an EXTERNAL project.             |
| **learn**  | `./sync learn auth-svc`                                | Synthesize lessons from a mission to update the shared knowledge base. |
| **deploy** | `./sync deploy auth-svc`                               | Create a GitHub repository and push the verified project.              |
| **stats**  | `./sync stats`                                         | View agent reliability, token usage, and engine performance metrics.   |

---

## Shared Intelligence & Documentation

For a deep-dive into the framework's internal mechanics, refer to:

* **[Complete Technical Guide](technical_documents/COMPLETE_GUIDE.md)**: AI fundamentals + every class and method explained.
* **[Architecture Map](technical_documents/architecture_map.md)**: System component diagrams and data flow.
* **[White Paper](technical_documents/WHITE_PAPER.md)**: Conceptual philosophy and agentic data flow.
* **[Free Setup Guide](technical_documents/FREE_SETUP.md)**: Hardware tuning and local-first strategies.
* **[Project Roadmap](technical_documents/tasks.txt)**: Development phases and upcoming features.
