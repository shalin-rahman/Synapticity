# Skill: Zero-Defect Software Engineering
# Focus: Writing immortal, self-documenting, and resilient source code.

## Playbook Strategy:
1. **SOLID Foundations**:
   - **Single Responsibility**: Every class/function does ONE thing perfectly.
   - **Open/Closed**: Design for extension without modification.
2. **DRY (Don't Repeat Yourself)**: If logic appears twice, abstract it into a utility or base class.
3. **Defensive Programming**:
   - Validate every input.
   - Handle every exception specifically (no bare `except`).
   - Use type hints for all parameters and return values.
4. **Maintenance-First Mindset**: Use descriptive naming (`mission_status` over `ms`). Write code as if the person reading it is a violent psychopath who knows where you live.

## Critical Thinking Guardrails:
- "Can I test this logic in isolation?"
- "Is this implementation the simplest possible solution?"
- "What happens if the model response is malformed or empty?"
