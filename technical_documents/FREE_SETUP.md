# 🌿 Synapticity: Free & Open-Source Setup

This guide explains how to run the Synapticity framework entirely locally and for free, bypassing all API costs while maintaining high-intelligence capabilities.

### 1. The Core Components
*   **Gemma 4 (or Llama 3 / Qwen 2.5)**: These are "Open Weights" models that act as the primary engine for the framework. They are free to download and run without subscription fees.
*   **Ollama**: The local inference server that hosts your chosen models. It provides the "brain" for the framework on your own hardware.
*   **Local Intelligence Routing**: The framework is architected to utilize Ollama's local endpoints as the primary driver, ensuring that all planning, coding, and verification tasks stay on your machine.

### 2. Why it Works
By using the **Local-First** toggle in Synapticity, the agents (Project Manager, Software Engineer, etc.) communicate directly with your local Ollama instance. This provides:
*   **Zero Costs**: No tokens-per-minute or monthly fees.
*   **Absolute Privacy**: Your source code and project specs never leave your local workspace.
*   **Offline Capability**: Develop complex software missions even without an internet connection.

### 4. Claude Code Parity
Users familiar with tools like **Claude Code** will find Synapticity provides a similar professional-grade agentic experience. The key difference is the backend:
*   Instead of Anthropic's paid API, Synapticity routes the same complex reasoning instructions to your local Ollama endpoint.
*   This grants you the same "Principal Engineer" level autonomy provided by cloud models, but running on your own GPU/CPU for free.

### 3. Quick Configuration
To enforce this setup, ensure your `.env` contains:
```env
OLLAMA_ACTIVE=True
GEMINI_ACTIVE=False
CLAUDE_ACTIVE=False
OLLAMA_MODEL=gemma4:latest
```

---
*Developed for autonomous excellence at zero cost.*
