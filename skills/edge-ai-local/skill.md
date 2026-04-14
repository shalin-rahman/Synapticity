# Skill: Local-First AI & Edge Intelligence
# Usage: Use when designing offline-capable agents, optimizing hardware constraints, or utilizing local runners like Ollama.

## 🖥️ Local-First Architecture
- **The Hybrid Strategy**: Use fast, small local models (via Ollama/vLLM) for high-frequency, low-latency tasks (like fast RAG retrieval, sentiment analysis, or routing). Fall back to massive cloud models (Gemini/Claude) only for heavy cognitive reasoning or complex code generation.
- **Privacy by Default**: Process sensitive data entirely on the host machine. This eliminates network latency and bypasses cloud compliance overhead.

## 📉 Quantization Engineering
- **Model Compression**: Understand that running FP16 (16-bit floating point) models natively requires immense VRAM. 
- Use Quantization (GGUF format) to compress weights into 8-bit, 4-bit, or even 2-bit spaces.
- **The Trade-off**: Recognize that quantizing below 4-bit (e.g., Q3_K) often severely damages the model's ability to reliably format JSON or write compilable code, even if general reasoning seems intact.

## ⚡ Inference Optimization
- **KV Cache**: The Key-Value cache stores past token calculations. For agents with continuous memory, monitor RAM usage closely as the KV cache grows linearly with conversation length.
- **GPU Offloading**: Ensure frameworks (like llama.cpp) are configured to offload as many layers to the native GPU (Metal/CUDA) as physically possible to maintain token-per-second (t/s) speed.

## 🚫 Edge AI Anti-Patterns
- Blindly defaulting to the largest model (e.g., 70B parameter models) on constrained developer laptops, resulting in unusable 1 t/s speeds. Start small (8B) and scale up only if reasoning fails.
- Ignoring context limits. Local models often have hard context boundary limits (e.g., 4096 or 8k). Exceeding this causes the runner to truncate or crash.
