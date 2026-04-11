# Skill: LLM Engineering & Advanced Prompting
# Usage: Use when crafting System Prompts, optimizing context windows, or building robust LLM interactions.

## 🧠 Cognitive Optimization
- **Chain of Thought (CoT)**: Force the LLM to explain its reasoning *before* arriving at an answer. (e.g., "Think step-by-step inside `<thought>` tags before outputting the final JSON"). This significantly improves complex logic.
- **Few-Shot Prompting**: Provide 2-3 high-quality examples of the exact input-to-output mapping you expect. Show, don't just tell.
- **Role-Prompting**: Establish a clear persona. "You are an expert Staff Security Engineer..." This sets the probabilistic weights toward higher-quality, domain-specific outputs.

## 📦 Context Management
- **The Information Funnel**: Put the most critical instructions (System Prompt) at the very top, and the specific task/data at the very bottom. LLMs suffer from "lost in the middle" syndrome.
- **Context Pruning**: Never blindly dump entire codebases or logs into the context. Use tools to grep, summarize, or extract only the relevant chunks before feeding to the LLM.
- **XML/Markdown Framing**: Use clear delimiters (`<data>`, `"""`, `## Section`) to separate instructions from raw data to prevent prompt injection or confusion.

## 🛡️ Robustness & Output Parsing
- **JSON Enforcement**: If you need JSON, provide a schema, use the model's native JSON mode (if available), and explicitly tell it to output ONLY valid JSON without markdown wrapping.
- **Failsafes**: Always wrap LLM API calls in robust retry blocks (e.g., Tenacity) with exponential backoff for 429s (Rate Limits) and 500s.
- **Validation**: Pass the LLM output through Pydantic or a schema validator immediately. If it fails, auto-reprompt the LLM with the validation error.

## 🚫 Prompting Anti-Patterns
- **Vague Instructions**: Using subjective words like "make it better" or "write good code." Be explicit: "Refactor to O(n) complexity and add MyPy typings."
- **Negative Prompting**: Telling the model what *not* to do (e.g., "Don't use loops") is less effective than telling it what *to* do (e.g., "Use recursion").
