# Synapticity Framework (v3.3)

Synapticity is a tool that builds software projects automatically. Instead of just writing snippets, it uses a team of AI agents to handle the whole job — from planning and coding to testing and launching.

It can run entirely on your own computer using **Ollama**, or connect to cloud models like **Gemini** and **Claude**.

---

## Recent Updates (v3.3.0)

Version 3.3.0 adds structural improvements to make the system more stable, faster, and easier to use. Here is what’s new:

- **Plain Simple English:** All documentation, CLI messages, and system logs are direct and human-friendly. The update removes complex AI jargon in favor of clear language.
- **Smart Model Routing:** A new internal router automatically picks the best AI model available based on settings and project history.
- **Unified State Management:** State saving and loading is faster and more reliable, with better recovery if a file is corrupted.
- **Simplified Project Output:** The system generates a **PROJECT_GUIDE.md** instead of technical docs, making it easier to hand over the work.
- **Updated Requirements:** All necessary tools are included in the requirements list for a smoother setup.

---

## How it Works

### 1. Constant Testing
The system won't finish a project until it passes every test. If there's a bug or a security hole, the AI tries to fix it automatically in a loop.

### 2. Expert Playbooks
The agents use "Skills" — specific sets of rules for things like FastAPI, React, or security. This helps them follow best practices without you having to explain them every time.

### 3. Live Research (Roadmap)
In the upcoming v3.4 release, the system will use **Firecrawl** to look up documentation on the web. This will help the AI learn about new libraries released after its training was finished.

### 4. Fast Local Running
Synapticity can run local models (like Gemma 4) at high speed. It keeps models loaded in memory so they respond instantly for free.

---

## Troubleshooting

- **Model is slow:** Make sure the AI model fits in your GPU memory (VRAM). If it uses regular RAM, it will be much slower.
- **API Errors:** Run `./sync doctor` to check your keys and internet connection.
- **Permission Denied:** If on Windows, try running your terminal as Administrator.
- **Ollama not found:** Ensure Ollama is running in your taskbar before starting a mission.

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
