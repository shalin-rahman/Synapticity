# Skill: Multi-Agent Orchestration
# Usage: Use when coordinating multiple specialized LLM agents to solve complex, multi-step problems.

## 🎭 Agent Personas & Specialization
- Give each agent a narrow, deep specialization rather than making one "God Agent". 
- Distinguish between **Planners** (Strategy, breaking down tasks), **Executors** (Coding, Writing), and **Evaluators** (QA, Security, Auditing).
- Ensure explicit hand-offs between agents.

## 🖇️ Orchestration Patterns
- **Sequential Routing (Waterfall)**: Agent A finishes -> Passes output to Agent B -> Passes to Agent C. Good for well-defined pipelines (e.g., Spec -> Code -> Test).
- **Hierarchical/Managerial**: A Manager agent receives the abstract goal, delegates specific tasks to Worker agents, reviews their work, and synthesizes the final output.
- **Consensus/Debate**: Multiple agents (with different system prompts or models) tackle the same problem, and an Arbitrator agent determines the best solution or merges them.

## 🛣️ State & Context Management (The "Blackboard")
- Implement a shared "Context Blackboard" or State Object.
- Agents should not just pass raw text strings to each other. They should read from and write to a structured state engine (e.g., updating a specific field in a JSON object).
- Maintain an "Audit Trail" so later agents (and human operators) can see *why* an earlier agent made a decision.

## 🛑 Control Flow & Halting
- **The Critic Loop**: Always pair a generation agent with a critic agent. The generator produces, the critic evaluates, and gives feedback. 
- Implement explicit halting conditions. The manager agent must have a tool specifically named `FinishTask(final_answer)` to signal the workflow is complete and escape the ReAct loop.
- Guard against "Agent Death Spirals" where two agents get stuck arguing or repeating the same error. Implement hard iteration limits.
