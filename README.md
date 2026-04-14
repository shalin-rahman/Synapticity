# Synapticity Framework (v3.0)

Synapticity is an autonomous development platform that manages the entire software lifecycle. It acts as a digital engineering team, coordinating specialized agents to handle planning, coding, security auditing, and deployment. By combining local processing (via Ollama) with cloud-based fallback (via Gemini), it provides a secure and resilient environment for software production.

---

## Core Philosophy & Best Practices

Synapticity is more than just a code generator; it implements a structured workflow modeled after professional engineering standards. For the best experience, keep these principles in mind:

### 1. You are the Lead Architect
While the system is autonomous, it is designed with a "Human-In-The-Loop" approach. 
- **Review Before Approving:** The system pauses at major milestones (like architectural planning and implementation). Always check the `MISSION_LOG.md` in your workspace before authorizing the next phase.
- **Audit the Path:** Use the `./sync audit` command to see exactly how the agents arrived at a decision.

### 2. Focus on Scoped Objectives
Autonomous agents perform best when their goals are clear and well-defined.
- **Start Small:** Begin by generating foundational scaffolding.
- **Refine as You Go:** If the project needs to pivot, use the `./sync update` command to re-draft specifications without losing your progress.

### 3. Surgical Tasks
You don't always need to run a full development cycle. You can dispatch a single agent for specific tasks, like refactoring a file or expanding documentation, using the standalone agent command.

---

## 🌿 The "Free-Forever" Setup
Synapticity is optimized for users who want to bypass private API costs associated with tools like Claude or GPT.

*   **Google's Gemma (or Qwen/Llama):** Acts as the open-weights "engine," which is free to download and run.
*   **Ollama:** Used to run these high-IQ models locally on your machine with zero latency.
*   **The Framework Advantage:** Synapticity is natively configured to use Ollama's local endpoints as the primary driver, providing a "Claude Code"-like experience without the Anthropic subscription fees.

---

## Getting Started

### 1. Installation
Install the core dependencies:

```bash
pip install google-genai requests python-dotenv rich pydantic-settings cryptography bandit pytest
```

### 2. Configuration
1. **Local LLM:** Install [Ollama](https://ollama.com/) and ensure the service is running locally (`http://localhost:11434`).
2. **Environment:** Copy `.env.example` to `.env`.
3. **Cloud Fallback:** Add your Gemini API keys if you want a fallback for complex reasoning tasks.

### 3. System Health Check
Run the doctor command to verify everything is connected correctly:
```bash
./sync doctor
```

---

## Command Reference

| Command | Usage Example | Description |
| :--- | :--- | :--- |
| **dash** | `./sync dash` | View active missions and their current status. |
| **launch** | `./sync launch auth-svc "Build a JWT API"`| Start a new development cycle. |
| **resume** | `./sync resume auth-svc` | Continue a paused mission. |
| **update** | `./sync update auth-svc "Add OAuth2 support"` | Adjust the objective and re-start the planning phase. |
| **audit** | `./sync audit auth-svc` | Review the internal task list and upcoming queues. |
| **agent** | `./sync agent auth-svc swe "Refactor utils.py"`| Send a specific agent for a one-off task. |
| **remove** | `./sync remove auth-svc` | Delete a mission workspace. |
| **review** | `./sync review bug-fix "security audit" C:/my-project` | Audit and patch an existing local project. |
| **learn**  | `./sync learn auth-svc` | Analyze mission history to improve future agent performance. |
| **deploy** | `./sync deploy auth-svc` | Create a GitHub repo and push the verified codebase. |

---

## Architecture & Security

Synapticity is built on a "Zero-Defect" philosophy:
1. **Sandboxed Execution:** All generated code is tested in an isolated environment before it ever touches your production workspace.
2. **Security Scans:** Passively runs vulnerability analysis (Bandit) against all implementation blocks.
3. **Self-Healing:** If code fails tests or scans, specialized QA agents identify the issue and instruct the Software Engineer to apply a fix automatically.

For more technical details, refer to the following resources in the [technical_documents](technical_documents/) directory:
*   **[Architecture Map](technical_documents/architecture_map.md)**: System design and state machine.
*   **[White Paper](technical_documents/WHITE_PAPER.md)**: The philosophy of the framework.
*   **[Free Setup Guide](technical_documents/FREE_SETUP.md)**: Running things for zero cost.
*   **[Project Roadmap](technical_documents/tasks.txt)**: Upcoming features and known issues.
