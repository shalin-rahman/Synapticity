# Skill: DevSecOps & Security Hardening
# Focus: Automating vulnerability detection and CI/CD resilience.

## Playbook Strategy:
1. **Security-by-Design**:
   - Least Privilege principle for all API interaction.
   - Always sanitize inputs and escape outputs.
2. **Automated Shielding**:
   - Mandatory Static Analysis (SAST) scanning.
   - Credentials detection (preventing secret leakage).
3. **Resilient CI/CD**:
   - YAML pipelines must be idempotent and fail-safe.
   - Include automated rollback strategies where applicable.
4. **Secrets Hygiene**: Never hardcode keys. Use environment variable resolution for all sensitive targets.

## Critical Thinking Guardrails:
- "If an attacker controls the input, what's the worst they can do?"
- "Is the pipeline protected from unauthorized overrides?"
- "Are we logging sensitive data in plain text?"
