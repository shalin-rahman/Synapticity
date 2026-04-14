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

### 4. Performance Optimization & Slowness Solutions
If you experience "Local model is taking a long time to load" or overall sluggishness, follow these industry-standard optimizations:

*   **VRAM Persistence (Keep-Alive)**: By default, Ollama unloads models after 5 minutes of inactivity. 
    *   **The Solution**: Set the environment variable `OLLAMA_KEEP_ALIVE=-1` on your OS. This locks the model in your GPU/RAM indefinitely, eliminating "Cold Start" delays.
    *   *Synapticity Hack*: The framework now automatically sends a "Warp Speed" pre-warming signal during startup to ensure the model is hot before your first mission begins.
*   **Hardware Alignment Check**: 
    *   Ensure your model fits entirely in **VRAM** (GPU memory). If it spills into System RAM or swap, performance drops by 10x-100x.
    *   Use **NVMe SSDs** for model storage. Mechanical HDDs cause extreme loading times.
*   **Context Window Tuning**: Synapticity uses a default `num_ctx: 8192`. If your hardware is older, try reducing this in `ollama.py` to `4096`.

### 5. Community & Documentation
For deep-dives into local AI performance and community support:
*   **Official Ollama Documentation**: [ollama.com/docs](https://ollama.com/docs)
*   **Troubleshooting Hub**: [Ollama GitHub Issues](https://github.com/ollama/ollama/issues)
*   **Community Forums**: 
    *   [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) (Best for hardware tuning)
    *   [Ollama Discord](https://discord.gg/ollama) (Real-time support)

---
*Developed for autonomous excellence at zero cost.*
