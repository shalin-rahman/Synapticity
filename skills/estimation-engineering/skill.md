# Skill: Professional Estimation Engineering
# Focus: Decomposing requirements into low-risk, data-driven effort estimates.

## Estimation Methodology:
1. **Document Ingestion**: Parse PDF/DOCX requirements documents to extract structured sections, tables, and requirement statements.
2. **Component Identification**: Group requirements into logical system components (API, UI, Database, Service, Infrastructure, Integration).
3. **Task Decomposition**: Break each component into granular, implementable tasks.
4. **PERT Analysis**: For each task, produce three estimates:
   - **Optimistic (O)**: Best-case scenario, no blockers.
   - **Likely (L)**: Realistic scenario, normal complexity.
   - **Pessimistic (P)**: Worst-case scenario, significant unknowns.
   - **Expected**: (O + 4L + P) / 6
5. **Risk Assessment**: Identify risk factors per task and apply multipliers.
6. **Dependency Mapping**: Determine which tasks block others (critical path).
7. **Skill Mapping**: Identify required technical skills for each task.

## Risk Multipliers:
- Integration with third-party: 1.5x
- Legacy system interaction: 1.6x
- Real-time processing: 1.5x
- Compliance requirements: 1.5x
- High availability: 1.4x
- Unknown technology: 1.7x
- Performance at scale: 1.3x

## Output Format:
- Executive Summary
- PERT Table (Optimistic / Likely / Pessimistic / Expected)
- 95% Confidence Interval
- Component Breakdown with tasks
- Risk Assessment
- Recommended Team Composition
- Critical Path
- Assumptions & Exclusions

## Critical Thinking Guardrails:
- "Are we double-counting effort across components?"
- "Have we accounted for testing and documentation?"
- "What are the integration points that could blow up the schedule?"
- "Is the team composition realistic for the tech stack?"

