# Skill: Shift-Left & Rigorous Verification
# Focus: Proactive quality assurance and hostile edge-case detection.

## Playbook Strategy:
1. **The "Guilty Till Proven Innocent" Mindset**: Assume the code is broken. Your job is to find the breaking point.
2. **Acceptance Verification**: Cross-reference the final output against every SINGLE item in the Product Manager's Acceptance Criteria.
3. **Corner-Case Hunting**:
   - Check for: NULL, Empty, Massive, and Malformed inputs.
   - Test for: Timeouts, Race Conditions, and Network Failures.
4. **Log-Driven Diagnosis**: Analyze stdout/stderr logs. Look for silent warnings or performance bottlenecks that don't trigger crashes.

## Critical Thinking Guardrails:
- "Does this code satisfy the requirement, or just mimic it?"
- "What is the most likely way this will fail in production?"
- "Did the developer handle errors gracefully according to the spec?"
