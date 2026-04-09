# Skill: Context Filter
# Usage: Use to pre-process large project requirements before sending to Local LLMs.

## Instructions:
1. **Extraction:** Identify only the technical entities, constraints, and business logic relevant to the CURRENT task.
2. **Pruning:** Remove conversational history, meeting notes, and redundant explanations.
3. **Structuring:** Present the filtered data in a "Key: Value" or "Requirement: Constraint" format.
4. **Token Efficiency:** The final output must be 5x smaller than the input while retaining 100% of the functional truth.

## Goal:
Minimize noise for the Local Software Engineer to prevent context-window "drift" or hallucinations.
