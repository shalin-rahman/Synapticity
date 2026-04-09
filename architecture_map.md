# 🗺️ synaptic 2.0: Architecture & Mission Map

This document serves as the "Source of Truth" for the The State of Intelligent Connection. It defines the hierarchy, data flow, and agent responsibilities to ensure architectural consistency.

## 📁 Repository Structure

```text
.
├── agents/             # 🧠 Intelligence Personas (Markdown)
│   ├── orchestrator.md  # CEO: Strategy & Delegation
│   ├── product-manager.md # Architect: Specs & Acceptance Criteria
│   ├── software-engineer.md # Coder: Human-idiomatic Implementation
│   ├── tester.md        # QA: Runtime validation & Logic checks
│   ├── oncall-engineer.md # SRE: Zero-trust security audit
│   └── writer.md        # Docs: Technical hand-off & referencing
├── synaptic/               # ⚙️ Core Framework (Python)
│   ├── core/            # Workflow, Gating, and Runtime engines
│   ├── models/          # Cloud (Gemini) & Local (Ollama) adapters
│   └── utils/           # Persistence, Hashing, Doctor, and Logger
├── tests/               # 🧪 Quality Assurance (Pytest)
├── skills/              # 📚 Technical Playbooks (Expert Knowledge)
│   ├── nextjs-expert/   # App Router & RSC patterns
│   ├── fastapi-expert/  # Async & Pydantic v2 patterns
│   ├── sqlalchemy-expert/ # Modern ORM 2.0 patterns
│   ├── typescript-clean/ # Enterprise-grade TS safety
│   └── pytest-modern/   # Professional testing fixtures
├── logs/                # 🔍 Audit Telemetry (synaptic.log)
├── workspace/           # 🏗️ Mission Isolated Environments
└── main.py              # 🎮 Command Center entry point
```

## 🔄 Mission Lifecycle (The State Machine)

synaptic follows a strictly gated sequential workflow with integrated checkpointing:

1.  **INITIALIZE**: Load mission goal and previous state (if any).
2.  **PLANNING**: `product-manager.md` drafts specs ➔ **Operator Approval**.
3.  **DEVELOPMENT**: `software-engineer.md` writes code (with Skill Injection) ➔ **Operator Approval**.
4.  **VERIFICATION**: 
    - `RuntimeRunner` executes code and captures REAL logs.
    - `tester.md` validates against specs.
    - `oncall-engineer.md` performs security audit.
5.  **HEALING**: If verification fails, the loop triggers up to 3 remediation attempts.
6.  **FINALIZATION**: `writer.md` generates technical docs ➔ Files saved to `workspace/`.

## 🧬 Agent Personas (World-Class Standards)

| Agent | Tier | Responsibility |
| :--- | :--- | :--- |
| **Orchestrator** | Staff Architect | Decides mission strategy and skill selection. |
| **PM** | Product Lead | Translates vague needs into rigorous AC and edge cases. |
| **SWE** | Staff Engineer | Produces "Human-Indistinguishable" idiomatic code. |
| **Tester** | SDET Lead | Validates logic using real runtime feedback. |
| **On-Call** | Security/SRE | Guards against OWASP, secrets, and logic flaws. |
| **Writer** | Tech Writer | Documents "Why" and "How" for professional hand-off. |

## 🛡️ Stability & Safety Guardrails
- **HITL Gating**: Mandatory operator approval at mission milestones.
- **Multi-Key Rotation**: Spreading traffic across 10 Gemini accounts (v2.0).
- **Hardened Runtime**: Executing AI code in a temp sandbox with `Bandit` security scanning.
- **synaptic Doctor**: Built-in diagnostic suite (`sync doctor`) for environment health.
- **Audit Logging**: Full telemetry history in `logs/synaptic.log`.
