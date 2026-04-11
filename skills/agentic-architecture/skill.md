# Skill: Agentic Architecture & ReAct Patterns
# Usage: Use when designing autonomous agents, tool-calling pipelines, or LLM-driven workflows.

## 🤖 Core Agent Architecture
- **Perception/Input**: The mechanism by which the agent receives state (Prompts, Vision, API payloads).
- **Cognition/Brain**: The LLM determining the next action based on its System Prompt and context.
- **Action/Tools**: The deterministic execution of commands (API calls, file writes, code execution).
- **Memory**: 
  - *Short-Term*: The immediate conversation/context window.
  - *Long-Term*: Vector databases or persistent stores for past interactions.

## 🔄 The ReAct Paradigm (Reason + Act)
Build agents that interleave reasoning with taking actions.
1. **Thought**: The LLM explicitly reasons about what it needs to do next. (e.g., "I need to find the user's ID to fetch their orders.")
2. **Action**: The LLM outputs a structured command to invoke a tool. (e.g., `CallTool: SearchUser(name="Alice")`)
3. **Observation**: The system executes the tool and returns the deterministic result to the LLM.
4. **Repeat**: The LLM repeats this cycle until the overarching goal is achieved.

## 🛠️ Tool Calling (Function Calling)
- **Strict Schemas**: Define tools using strict JSON schemas (OpenAPI style) to ensure the LLM understands expected inputs.
- **Atomic Tools**: Tools should do exactly one thing well. Avoid mega-tools with overly complex parameters.
- **Error Feedback**: If a tool fails (e.g., 404, type error), feed the explicit error message back into the LLM as an Observation so it can self-correct.

## 🚫 Anti-Patterns in Agent Design
- **Assuming Determinism**: Never assume the LLM will output the exact same JSON format twice without strict enforcement (like JSON grammar parsing).
- **Infinite Loops**: Always implement a `max_iterations` or budget limit on the ReAct loop to prevent the agent from getting stuck.
- **Dangerous Auto-Run**: Never allow an agent to execute destructive actions (DELETE, DROP, execute arbitrary shell code) without human-in-the-loop approval or strict sandboxing.
