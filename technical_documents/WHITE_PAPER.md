# Synapticity: Technical Framework Overview (v3.1)

## Executive Summary

Synapticity is an autonomous software development framework built for production use. Think of it as a bridge between your high-level ideas and a verified, ready-to-use codebase. By orchestrating a specialized team of AI agents, it essentially automates the entire software factory process—from planning the initial architecture all the way to deploying it with cloud-native CI/CD pipelines.

### The "Smart Factory" Model
Rather than a chat assistant, Synapticity treats software development like a rigorous manufacturing process:
- **Core Reasoning**: We use high-density local and cloud-based Large Language Models (LLMs) to power the team.
- **Service Adapters**: Pluggable interfaces allow us to easily swap between Ollama (local), Gemini, and Claude.
- **Specialized Personas**: Our agents act like a real team (Product Manager, Software Engineer, QA, Security), each with their own unique expertise and constraints.
- **Dynamic Playbooks**: We inject domain-specific "Skills" directly into the agents' context right when they need them.
- **Self-Healing Loop**: If something breaks, the verification agents flag the issue, and the system automatically remediates the code in a secure sandbox.


---

## Intelligence & Workflow Architecture

The framework operates on a state-machine orchestrator that strictly enforces a "Verification-First" culture. We guarantee that no mission code is finalized until it successfully passes through both functional and security testing gates.


```mermaid
graph TD
    User([Mission Objective]) --> PM[Product Manager]
    PM -->|Technical Specs| SWE[Software Engineer]
    
    subgraph "The Healing Cycle (Parallel Verification)"
        SWE -->|Code Artifacts| Runner[Runtime Sandbox]
        Runner -->|Stdout/Stderr/Logs| QA[Tester Agent]
        Runner -->|Security SAST| Sec[Security Auditor]
        
        QA -->|Functional Repairs| SWE
        Sec -->|Security Patches| SWE
    end
    
    QA & Sec -->|Dual PASS Verdict| Writer[Documentation]
    Writer -->|Docs| DevOps[DevOps Engineer]
    DevOps -->|Actions YAML| Git[Autonomous Git/GitHub Deployment]
    
    Git -->|Mission Logs| Reflector[Reflection Engine]
    Reflector -->|New Lessons| Skills[Shared Knowledge Base]
```

### Component Innovation
- **Asynchronous Monitoring**: We use background heartbeats and non-blocking model pre-warming to ensure the CLI status updates instantly without any noticeable lag.
- **Parallel Dispatch**: The Healing Cycle sends out the Functional QA and Security Audit tasks at exactly the same time, which cuts down the total verification time immensely.
- **Meta-Cognition Reflection**: After a mission finishes, a Reflection Engine looks back at the interactions to automatically synthesize new "Lessons." This allows the team to literally self-improve from task to task.

---

## Design Philosophy: SOLID & Agentic

We wrote this framework closely adhering to **SOLID** and **DRY** development principles:
- **Single Responsibility**: Every part has its lane. Individual managers handle state, logs, workspace, and model communication independently.
- **Dependency Inversion**: Our high-level orchestration doesn't care whether you're using Gemini or Ollama; it's completely decoupled.
- **Open-Closed Pattern**: Want to add a new command, agent, or model adapter? You can register them via a unified dispatch registry without needing to mess with the core logic.

---

## The Specialized Agent Pool

1.  **Product Manager**: Goal-to-AC translation and architectural blueprinting.
2.  **Software Engineer**: Precision-engineered, zero-defect source code synthesis.
3.  **Tester Agent**: Structural and functional validation via real-world sandbox execution.
4.  **Security Auditor**: Vulnerability containment and static analysis (Bandit).
5.  **Technical Writer**: Narrative documentation and technical hand-off generation.
6.  **DevOps Engineer**: GitHub Actions synthesis and autonomous deployment pipelines.

---

## Security & Operational Guardrails

- **Warp-Speed Pre-warming**: Models are loaded into VRAM on startup to eliminate "Cold Start" latency.
- **Infinite Residency**: Models are locked in memory using `-1 keep_alive` for zero-cost instant response.
- **Isolated Sandboxing**: All generated code is executed in a temporary, isolated runtime before verification.
- **Administrator Gateway**: Critical operations (e.g., skill ingestion) are protected by a secure CLI passcode gate.

For deeper technical mapping, refer to the [architecture_map.md](architecture_map.md).
