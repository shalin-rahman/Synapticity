"""
Estimation Engine — professional-grade project estimation preparation.
Reads documents, identifies tasks/subtasks/components/dependencies/skills,
and produces low-risk effort estimates with confidence intervals.
LLM refinement (refine_with_ai) adjusts heuristic PERT numbers using
the actual document requirements as context.
"""

import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from synaptic.utils.document_parser import DocumentParser, ParsedDocument
from synaptic.utils.formatting import strip_markdown_backticks
from synaptic.utils.logger import synaptic_log


@dataclass
class TaskEstimate:
    """Individual task with effort estimate and risk assessment."""
    id: str
    title: str
    description: str
    category: str
    optimistic_hours: float
    likely_hours: float
    pessimistic_hours: float
    dependencies: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    mitigation: str = ""

    @property
    def expected_hours(self) -> float:
        """PERT weighted average: (O + 4L + P) / 6"""
        return (self.optimistic_hours + 4 * self.likely_hours + self.pessimistic_hours) / 6

    @property
    def standard_deviation(self) -> float:
        """Standard deviation for risk calculation: (P - O) / 6"""
        return (self.pessimistic_hours - self.optimistic_hours) / 6

    @property
    def confidence_95(self) -> Tuple[float, float]:
        """95% confidence interval."""
        expected = self.expected_hours
        sd = self.standard_deviation
        return (expected - 2 * sd, expected + 2 * sd)


@dataclass
class ComponentBreakdown:
    """System component with its tasks and interfaces."""
    name: str
    description: str
    type: str
    tasks: List[TaskEstimate] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)


@dataclass
class ProjectEstimate:
    """Complete project estimation report."""
    project_name: str
    source_document: str
    generated_at: str
    summary: str
    components: List[ComponentBreakdown]
    total_optimistic: float
    total_likely: float
    total_pessimistic: float
    total_expected: float
    confidence_95_range: Tuple[float, float]
    risk_assessment: str
    recommended_team: List[str]
    critical_path: List[str]
    assumptions: List[str]
    exclusions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "source_document": self.source_document,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "components": [
                {
                    "name": c.name,
                    "description": c.description,
                    "type": c.type,
                    "tasks": [
                        {
                            "id": t.id,
                            "title": t.title,
                            "description": t.description,
                            "category": t.category,
                            "optimistic_hours": t.optimistic_hours,
                            "likely_hours": t.likely_hours,
                            "pessimistic_hours": t.pessimistic_hours,
                            "expected_hours": round(t.expected_hours, 2),
                            "dependencies": t.dependencies,
                            "required_skills": t.required_skills,
                            "risk_factors": t.risk_factors,
                            "mitigation": t.mitigation
                        }
                        for t in c.tasks
                    ],
                    "interfaces": c.interfaces,
                    "tech_stack": c.tech_stack
                }
                for c in self.components
            ],
            "totals": {
                "optimistic_hours": self.total_optimistic,
                "likely_hours": self.total_likely,
                "pessimistic_hours": self.total_pessimistic,
                "expected_hours": round(self.total_expected, 2),
                "confidence_95_low": round(self.confidence_95_range[0], 2),
                "confidence_95_high": round(self.confidence_95_range[1], 2)
            },
            "risk_assessment": self.risk_assessment,
            "recommended_team": self.recommended_team,
            "critical_path": self.critical_path,
            "assumptions": self.assumptions,
            "exclusions": self.exclusions
        }


class EstimationEngine:
    """
    Professional-grade estimation preparation engine.
    Decomposes requirements into tasks, identifies dependencies,
    assesses risks, and produces PERT-based estimates.
    """

    SKILL_MAP = {
        'frontend': ['react', 'vue', 'angular', 'typescript', 'css', 'html', 'ui/ux'],
        'backend': ['python', 'java', 'nodejs', 'fastapi', 'django', 'spring', 'api-design'],
        'database': ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'sqlalchemy', 'orm'],
        'devops': ['docker', 'kubernetes', 'ci/cd', 'aws', 'azure', 'terraform', 'github-actions'],
        'testing': ['pytest', 'jest', 'cypress', 'selenium', 'unit-testing', 'integration-testing'],
        'documentation': ['technical-writing', 'api-docs', 'swagger', 'openapi'],
        'security': ['oauth', 'jwt', 'encryption', 'bandit', 'penetration-testing'],
        'ai/ml': ['llm-engineering', 'rag', 'embeddings', 'pytorch', 'tensorflow']
    }

    RISK_INDICATORS = {
        'integration': 1.5,
        'third-party': 1.4,
        'legacy': 1.6,
        'real-time': 1.5,
        'high-availability': 1.4,
        'compliance': 1.5,
        'scale': 1.3,
        'unknown': 1.7
    }

    def __init__(self):
        self._parser = DocumentParser()
        self._last_doc: Optional[ParsedDocument] = None

    def prepare_estimate(self, document_path: str, project_name: Optional[str] = None) -> ProjectEstimate:
        """Main entry point: read a document and produce a complete estimation."""
        synaptic_log.info(f"Preparing estimate for: {document_path}")

        doc = self._parser.parse(document_path)
        self._last_doc = doc
        requirements = self._parser.extract_requirements(doc)
        components = self._identify_components(doc, requirements)

        for component in components:
            component.tasks = self._decompose_tasks(component, requirements)

        self._calculate_dependencies(components)
        totals = self._calculate_totals(components)
        risk_assessment = self._assess_risks(components)
        critical_path = self._identify_critical_path(components)
        team = self._recommend_team(components)

        return ProjectEstimate(
            project_name=project_name or doc.title or "Untitled Project",
            source_document=os.path.basename(document_path),
            generated_at=datetime.now().isoformat(),
            summary=self._generate_summary(doc, components),
            components=components,
            total_optimistic=totals['optimistic'],
            total_likely=totals['likely'],
            total_pessimistic=totals['pessimistic'],
            total_expected=totals['expected'],
            confidence_95_range=totals['confidence_95'],
            risk_assessment=risk_assessment,
            recommended_team=team,
            critical_path=critical_path,
            assumptions=self._extract_assumptions(doc),
            exclusions=self._extract_exclusions(doc)
        )

    def _identify_components(self, doc: ParsedDocument, requirements: List[Dict]) -> List[ComponentBreakdown]:
        """Identify system components from document structure and requirements."""
        components = []

        for section in doc.sections:
            comp_type = self._detect_component_type(section.title + " " + section.content)
            if comp_type:
                desc = section.content[:200] + "..." if len(section.content) > 200 else section.content
                components.append(ComponentBreakdown(
                    name=section.title,
                    description=desc,
                    type=comp_type,
                    tech_stack=self._detect_tech_stack(section.content)
                ))

        if not components:
            components = self._infer_components_from_requirements(requirements)

        return components

    def _detect_component_type(self, text: str) -> Optional[str]:
        """Detect component type from text analysis."""
        text_lower = text.lower()
        type_indicators = {
            'api': ['api', 'endpoint', 'rest', 'graphql', 'microservice'],
            'database': ['database', 'schema', 'table', 'storage', 'persistence'],
            'ui': ['ui', 'frontend', 'interface', 'screen', 'page', 'component'],
            'service': ['service', 'backend', 'server', 'business logic', 'processor'],
            'infrastructure': ['infrastructure', 'deployment', 'pipeline', 'docker', 'kubernetes'],
            'integration': ['integration', 'webhook', 'sync', 'connector', 'adapter']
        }

        for comp_type, indicators in type_indicators.items():
            if any(ind in text_lower for ind in indicators):
                return comp_type
        return 'service'

    def _detect_tech_stack(self, text: str) -> List[str]:
        """Detect technology stack mentions in text."""
        tech_patterns = {
            'python': r'\bpython\b',
            'fastapi': r'\bfastapi\b',
            'django': r'\bdjango\b',
            'react': r'\breact\b',
            'vue': r'\bvue\.?js?\b',
            'angular': r'\bangular\b',
            'typescript': r'\btypescript\b',
            'postgresql': r'\bpostgres(ql)?\b',
            'mysql': r'\bmysql\b',
            'mongodb': r'\bmongodb\b',
            'redis': r'\bredis\b',
            'docker': r'\bdocker\b',
            'kubernetes': r'\bkubernetes\b',
            'aws': r'\baws\b',
            'azure': r'\bazure\b',
            'terraform': r'\bterraform\b',
            'github-actions': r'\bgithub\s+actions\b',
            'pytest': r'\bpytest\b',
            'jest': r'\bjest\b'
        }

        found = []
        text_lower = text.lower()
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, text_lower):
                found.append(tech)
        return found

    def _infer_components_from_requirements(self, requirements: List[Dict]) -> List[ComponentBreakdown]:
        """Infer components when document structure is unclear."""
        categories = {}
        for req in requirements:
            cat = self._categorize_requirement(req['text'])
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(req)

        components = []
        for cat, reqs in categories.items():
            components.append(ComponentBreakdown(
                name=f"{cat.title()} Component",
                description=f"Contains {len(reqs)} related requirements",
                type=cat,
                tech_stack=[]
            ))
        return components

    def _categorize_requirement(self, text: str) -> str:
        """Categorize a requirement text into component type."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['ui', 'screen', 'page', 'button', 'form', 'display']):
            return 'ui'
        if any(kw in text_lower for kw in ['api', 'endpoint', 'request', 'response']):
            return 'api'
        if any(kw in text_lower for kw in ['database', 'store', 'save', 'query', 'table']):
            return 'database'
        if any(kw in text_lower for kw in ['deploy', 'pipeline', 'docker', 'build']):
            return 'infrastructure'
        return 'service'

    def _decompose_tasks(self, component: ComponentBreakdown, requirements: List[Dict]) -> List[TaskEstimate]:
        """Decompose a component into granular tasks with PERT estimates."""
        tasks = []
        task_id = 0
        task_templates = self._get_task_templates(component.type)

        for template in task_templates:
            task_id += 1
            risk_multiplier = self._calculate_risk_multiplier(template['description'])

            tasks.append(TaskEstimate(
                id=f"{component.type[:3].upper()}-{task_id:03d}",
                title=template['title'],
                description=template['description'],
                category=component.type,
                optimistic_hours=template['base_hours'] * 0.7 * risk_multiplier,
                likely_hours=template['base_hours'] * risk_multiplier,
                pessimistic_hours=template['base_hours'] * 1.5 * risk_multiplier,
                required_skills=self._map_skills(component.type, component.tech_stack),
                risk_factors=self._identify_risk_factors(template['description']),
                mitigation=self._suggest_mitigation(template['description'])
            ))

        return tasks

    def _get_task_templates(self, component_type: str) -> List[Dict]:
        """Get standard task templates for a component type."""
        templates = {
            'api': [
                {'title': 'API Design & Specification', 'description': 'Design REST/GraphQL endpoints, request/response schemas, OpenAPI spec', 'base_hours': 8},
                {'title': 'Core Endpoint Implementation', 'description': 'Implement business logic endpoints with validation and error handling', 'base_hours': 16},
                {'title': 'Authentication & Authorization', 'description': 'Implement JWT/OAuth2 security, role-based access control', 'base_hours': 12},
                {'title': 'API Testing & Documentation', 'description': 'Unit tests, integration tests, API documentation generation', 'base_hours': 10}
            ],
            'ui': [
                {'title': 'Component Architecture', 'description': 'Design component hierarchy, state management, routing', 'base_hours': 8},
                {'title': 'Core UI Implementation', 'description': 'Implement screens, forms, data display components', 'base_hours': 20},
                {'title': 'Styling & Responsiveness', 'description': 'CSS/Tailwind implementation, mobile responsiveness', 'base_hours': 12},
                {'title': 'Frontend Testing', 'description': 'Component tests, E2E tests, accessibility checks', 'base_hours': 10}
            ],
            'database': [
                {'title': 'Schema Design', 'description': 'Design tables, relationships, indexes, constraints', 'base_hours': 8},
                {'title': 'Migration & Seeding', 'description': 'Create migrations, seed data, rollback scripts', 'base_hours': 6},
                {'title': 'Query Optimization', 'description': 'Optimize queries, add indexes, performance tuning', 'base_hours': 10},
                {'title': 'Data Access Layer', 'description': 'Implement repositories, ORM models, data validation', 'base_hours': 12}
            ],
            'service': [
                {'title': 'Service Architecture', 'description': 'Design service boundaries, interfaces, data flow', 'base_hours': 8},
                {'title': 'Core Business Logic', 'description': 'Implement domain logic, workflows, state machines', 'base_hours': 20},
                {'title': 'Integration Layer', 'description': 'Connect to external services, APIs, message queues', 'base_hours': 14},
                {'title': 'Service Testing', 'description': 'Unit tests, mock external dependencies, contract tests', 'base_hours': 12}
            ],
            'infrastructure': [
                {'title': 'Environment Setup', 'description': 'Configure dev/staging/prod environments, networking', 'base_hours': 10},
                {'title': 'CI/CD Pipeline', 'description': 'Build, test, deploy automation, artifact management', 'base_hours': 12},
                {'title': 'Monitoring & Logging', 'description': 'Setup observability, alerts, log aggregation', 'base_hours': 8},
                {'title': 'Security Hardening', 'description': 'Network policies, secrets management, vulnerability scanning', 'base_hours': 10}
            ],
            'integration': [
                {'title': 'Integration Analysis', 'description': 'Analyze external APIs, data formats, rate limits', 'base_hours': 8},
                {'title': 'Adapter Implementation', 'description': 'Build adapters, transformers, error handling', 'base_hours': 16},
                {'title': 'Sync & Reliability', 'description': 'Handle failures, retries, idempotency, data consistency', 'base_hours': 14},
                {'title': 'Integration Testing', 'description': 'Mock external services, contract validation', 'base_hours': 10}
            ]
        }
        return templates.get(component_type, templates['service'])

    def _calculate_risk_multiplier(self, description: str) -> float:
        """Calculate risk multiplier based on description keywords."""
        multiplier = 1.0
        desc_lower = description.lower()
        for indicator, factor in self.RISK_INDICATORS.items():
            if indicator in desc_lower:
                multiplier = max(multiplier, factor)
        return multiplier

    def _map_skills(self, category: str, tech_stack: List[str]) -> List[str]:
        """Map component to required skills."""
        base_skills = self.SKILL_MAP.get(category, [])
        return list(set(base_skills + tech_stack))

    def _identify_risk_factors(self, description: str) -> List[str]:
        """Identify risk factors from description."""
        risks = []
        desc_lower = description.lower()
        risk_keywords = {
            'integration complexity': ['integration', 'third-party', 'external'],
            'performance requirements': ['performance', 'latency', 'throughput', 'scale'],
            'security concerns': ['security', 'authentication', 'authorization', 'encryption'],
            'unknown technology': ['new', 'unfamiliar', 'experimental', 'unknown'],
            'data migration': ['migration', 'legacy', 'existing data'],
            'real-time processing': ['real-time', 'streaming', 'live'],
            'compliance requirements': ['compliance', 'regulatory', 'gdpr', 'hipaa']
        }
        for risk, keywords in risk_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                risks.append(risk)
        return risks

    def _suggest_mitigation(self, description: str) -> str:
        """Suggest mitigation strategies for identified risks."""
        mitigations = []
        desc_lower = description.lower()

        if 'integration' in desc_lower or 'third-party' in desc_lower:
            mitigations.append("Build adapter pattern with circuit breaker")
        if 'performance' in desc_lower or 'scale' in desc_lower:
            mitigations.append("Implement caching and load testing early")
        if 'security' in desc_lower:
            mitigations.append("Conduct security review and penetration testing")
        if 'new' in desc_lower or 'experimental' in desc_lower:
            mitigations.append("Create proof-of-concept before full implementation")
        if 'migration' in desc_lower:
            mitigations.append("Plan rollback strategy and data validation")

        return "; ".join(mitigations) if mitigations else "Standard development practices"

    def _calculate_dependencies(self, components: List[ComponentBreakdown]) -> None:
        """Calculate inter-component dependencies."""
        for i, comp in enumerate(components):
            for j, other in enumerate(components):
                if i != j:
                    if comp.name.lower() in other.description.lower():
                        comp.interfaces.append(other.name)

            for k, task in enumerate(comp.tasks):
                if k > 0:
                    task.dependencies.append(comp.tasks[k-1].id)

    def _calculate_totals(self, components: List[ComponentBreakdown]) -> Dict[str, float]:
        """Calculate project-wide totals."""
        optimistic = sum(t.optimistic_hours for c in components for t in c.tasks)
        likely = sum(t.likely_hours for c in components for t in c.tasks)
        pessimistic = sum(t.pessimistic_hours for c in components for t in c.tasks)
        expected = sum(t.expected_hours for c in components for t in c.tasks)

        variance = sum(t.standard_deviation ** 2 for c in components for t in c.tasks)
        project_sd = variance ** 0.5

        return {
            'optimistic': optimistic,
            'likely': likely,
            'pessimistic': pessimistic,
            'expected': expected,
            'confidence_95': (expected - 2 * project_sd, expected + 2 * project_sd)
        }

    def _assess_risks(self, components: List[ComponentBreakdown]) -> str:
        """Generate overall risk assessment."""
        all_risks = []
        for comp in components:
            for task in comp.tasks:
                all_risks.extend(task.risk_factors)

        risk_counts = {}
        for risk in all_risks:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        if not risk_counts:
            return "Low risk project. Standard development practices sufficient."

        sorted_risks = sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)
        risk_lines = [f"- {risk}: {count} tasks affected" for risk, count in sorted_risks[:5]]

        return "Key Risks:\n" + "\n".join(risk_lines)

    def _identify_critical_path(self, components: List[ComponentBreakdown]) -> List[str]:
        """Identify tasks on the critical path (simplified)."""
        all_tasks = [(t, c.name) for c in components for t in c.tasks]
        all_tasks.sort(key=lambda x: x[0].expected_hours, reverse=True)
        return [f"{t.id}: {t.title} ({comp_name})" for t, comp_name in all_tasks[:5]]

    def _recommend_team(self, components: List[ComponentBreakdown]) -> List[str]:
        """Recommend team composition based on required skills."""
        all_skills = set()
        for comp in components:
            for task in comp.tasks:
                all_skills.update(task.required_skills)

        role_mapping = {
            'frontend': 'Frontend Developer',
            'backend': 'Backend Developer',
            'database': 'Database Engineer',
            'devops': 'DevOps Engineer',
            'testing': 'QA Engineer',
            'security': 'Security Engineer',
            'ai/ml': 'ML Engineer'
        }

        team = []
        for skill in all_skills:
            for key, role in role_mapping.items():
                if key in skill.lower() and role not in team:
                    team.append(role)

        core_roles = ['Tech Lead', 'Product Manager']
        for role in core_roles:
            if role not in team:
                team.insert(0, role)

        return team

    def _generate_summary(self, doc: ParsedDocument, components: List[ComponentBreakdown]) -> str:
        """Generate executive summary."""
        total_tasks = sum(len(c.tasks) for c in components)
        return (
            f"Project '{doc.title}' consists of {len(components)} major components "
            f"with {total_tasks} identified tasks. "
            f"Document analysis identified {len(doc.sections)} sections and "
            f"{len(doc.tables)} data tables."
        )

    def _extract_assumptions(self, doc: ParsedDocument) -> List[str]:
        """Extract assumptions from document."""
        assumptions = []
        text = doc.raw_text.lower()

        if 'assume' in text:
            sentences = re.split(r'[.!?]+', doc.raw_text)
            for sent in sentences:
                if 'assume' in sent.lower() or 'assumption' in sent.lower():
                    assumptions.append(sent.strip())

        if not assumptions:
            assumptions = [
                "Requirements are complete and stable",
                "Third-party services will be available",
                "Team has required technical skills",
                "No major architectural changes during development"
            ]

        return assumptions[:5]

    def _extract_exclusions(self, doc: ParsedDocument) -> List[str]:
        """Extract out-of-scope items from document."""
        exclusions = []
        text = doc.raw_text.lower()

        if 'out of scope' in text or 'not included' in text or 'exclusion' in text:
            sentences = re.split(r'[.!?]+', doc.raw_text)
            for sent in sentences:
                if any(kw in sent.lower() for kw in ['out of scope', 'not included', 'exclusion', 'not in scope']):
                    exclusions.append(sent.strip())

        if not exclusions:
            exclusions = [
                "Production deployment environment setup (unless specified)",
                "User training and documentation (unless specified)",
                "Third-party licensing costs",
                "Post-launch maintenance and support"
            ]

        return exclusions[:5]

    # ------------------------------------------------------------------
    # AI Refinement — LLM post-processes the heuristic PERT breakdown
    # ------------------------------------------------------------------

    async def refine_with_ai(
        self,
        estimate: ProjectEstimate,
        doc: ParsedDocument,
        model_adapter,
    ) -> ProjectEstimate:
        """
        Passes the document requirements + heuristic task breakdown to the LLM.
        The LLM returns adjustments and additional tasks grounded in the actual
        document context. Falls back to the original estimate on any failure.
        """
        system = self._load_estimation_persona()
        prompt  = self._build_refinement_prompt(estimate, doc)

        try:
            raw = await model_adapter.generate(system, prompt)
        except Exception as e:
            synaptic_log.warning(f"[ESTIMATE] AI refinement call failed: {e} — using heuristic estimate")
            return estimate

        try:
            refined = self._parse_ai_response(raw)
        except Exception as e:
            synaptic_log.warning(f"[ESTIMATE] AI response parse failed: {e} — using heuristic estimate")
            return estimate

        return self._apply_refinements(estimate, refined)

    # ------------------------------------------------------------------
    # Private AI helpers
    # ------------------------------------------------------------------

    def _load_estimation_persona(self) -> str:
        """Load the estimation-engineer agent persona."""
        from synaptic.config import settings
        persona_path = os.path.join(settings.AGENT_PATH, "estimation-engineer.md")
        if os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                return f.read()
        return "You are a senior project estimation engineer. Apply PERT methodology."

    def _build_refinement_prompt(self, estimate: ProjectEstimate, doc: ParsedDocument) -> str:
        """Build the LLM prompt combining document content with the heuristic task list."""
        # Cap document text to avoid overflowing context
        doc_text = (doc.raw_text[:3000] + "\n...[truncated]") if len(doc.raw_text) > 3000 else doc.raw_text

        # Compact task list — send only the fields the LLM needs to reason about
        task_summary = []
        for comp in estimate.components:
            for task in comp.tasks:
                task_summary.append({
                    "component": comp.name,
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "optimistic_hours": task.optimistic_hours,
                    "likely_hours": task.likely_hours,
                    "pessimistic_hours": task.pessimistic_hours,
                })

        return f"""You are refining a heuristic PERT estimate using the actual project requirements.

DOCUMENT REQUIREMENTS:
{doc_text}

CURRENT HEURISTIC TASK BREAKDOWN (JSON):
{json.dumps(task_summary, indent=2)}

Your job:
1. Review each task against the document. Adjust PERT hours where the document implies higher/lower complexity.
2. Add any tasks the heuristic missed that are clearly required by the document.
3. Write a refined executive summary grounded in the document content.
4. Extract any explicit assumptions or exclusions from the document text.

Return ONLY a valid JSON object — no prose, no markdown fences:
{{
  "adjusted_tasks": [
    {{
      "id": "<existing task id>",
      "optimistic_hours": <number>,
      "likely_hours": <number>,
      "pessimistic_hours": <number>,
      "reasoning": "<one sentence why>"
    }}
  ],
  "additional_tasks": [
    {{
      "component": "<existing component name or new>",
      "title": "<task title>",
      "description": "<what this task covers>",
      "optimistic_hours": <number>,
      "likely_hours": <number>,
      "pessimistic_hours": <number>,
      "risk_factors": ["<risk>"]
    }}
  ],
  "refined_summary": "<executive summary paragraph>",
  "additional_assumptions": ["<assumption>"],
  "additional_exclusions": ["<exclusion>"],
  "confidence": "low|medium|high"
}}"""

    def _parse_ai_response(self, raw: str) -> Dict[str, Any]:
        """Parse and validate the LLM JSON response."""
        cleaned = strip_markdown_backticks(raw).strip()
        # Find the outermost JSON object in case the model added prose
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if not match:
            raise ValueError("No JSON object found in LLM response")
        data = json.loads(match.group(0))
        # Validate required keys exist (partial responses still usable)
        for key in ("adjusted_tasks", "additional_tasks", "refined_summary"):
            if key not in data:
                data[key] = [] if key != "refined_summary" else ""
        return data

    def _apply_refinements(self, estimate: ProjectEstimate, refined: Dict[str, Any]) -> ProjectEstimate:
        """Merge LLM adjustments back into the ProjectEstimate."""
        # Build a flat task lookup by id for O(1) access
        task_by_id: Dict[str, TaskEstimate] = {
            task.id: task
            for comp in estimate.components
            for task in comp.tasks
        }

        # 1. Apply hour adjustments to existing tasks
        for adj in refined.get("adjusted_tasks", []):
            task = task_by_id.get(adj.get("id", ""))
            if not task:
                continue
            task.optimistic_hours  = float(adj.get("optimistic_hours",  task.optimistic_hours))
            task.likely_hours      = float(adj.get("likely_hours",      task.likely_hours))
            task.pessimistic_hours = float(adj.get("pessimistic_hours", task.pessimistic_hours))
            reasoning = adj.get("reasoning", "")
            if reasoning:
                task.mitigation = f"[AI] {reasoning}" if not task.mitigation else f"{task.mitigation}; [AI] {reasoning}"

        # 2. Append additional tasks to matching (or first) component
        comp_by_name: Dict[str, ComponentBreakdown] = {c.name: c for c in estimate.components}
        for extra in refined.get("additional_tasks", []):
            comp_name = extra.get("component", "")
            comp = comp_by_name.get(comp_name) or (estimate.components[0] if estimate.components else None)
            if not comp:
                continue
            task_num = len(comp.tasks) + 1
            comp.tasks.append(TaskEstimate(
                id=f"{comp.type[:3].upper()}-AI{task_num:02d}",
                title=extra.get("title", "AI-identified task"),
                description=extra.get("description", ""),
                category=comp.type,
                optimistic_hours=float(extra.get("optimistic_hours", 4)),
                likely_hours=float(extra.get("likely_hours", 8)),
                pessimistic_hours=float(extra.get("pessimistic_hours", 16)),
                risk_factors=extra.get("risk_factors", []),
            ))

        # 3. Refresh totals after mutations
        totals = self._calculate_totals(estimate.components)
        estimate.total_optimistic   = totals["optimistic"]
        estimate.total_likely       = totals["likely"]
        estimate.total_pessimistic  = totals["pessimistic"]
        estimate.total_expected     = totals["expected"]
        estimate.confidence_95_range = totals["confidence_95"]

        # 4. Enrich summary and assumptions with LLM content
        if refined.get("refined_summary"):
            estimate.summary = refined["refined_summary"]
        estimate.assumptions += [a for a in refined.get("additional_assumptions", []) if a not in estimate.assumptions]
        estimate.exclusions  += [e for e in refined.get("additional_exclusions",  []) if e not in estimate.exclusions]

        # 5. Tag the report as AI-refined
        ai_confidence = refined.get("confidence", "medium")
        estimate.risk_assessment = (
            f"[AI-Refined — confidence: {ai_confidence}]\n\n" + estimate.risk_assessment
        )

        return estimate

    def save_estimate(self, estimate: ProjectEstimate, output_dir: str) -> str:
        """Save estimation report to JSON and Markdown."""
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "estimate.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estimate.to_dict(), f, indent=2)

        md_path = os.path.join(output_dir, "ESTIMATION_REPORT.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_markdown_report(estimate))

        synaptic_log.info(f"Estimate saved to: {output_dir}")
        return output_dir

    def _generate_markdown_report(self, estimate: ProjectEstimate) -> str:
        """Generate professional Markdown estimation report."""
        lines = []
        lines.append("# Project Estimation Report")
        lines.append("")
        lines.append(f"## {estimate.project_name}")
        lines.append("")
        lines.append(f"**Source Document:** {estimate.source_document}")
        lines.append(f"**Generated:** {estimate.generated_at}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(estimate.summary)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Effort Estimate (PERT)")
        lines.append("")
        lines.append("| Metric | Hours | Days (8h) | Weeks (5d) |")
        lines.append("|--------|-------|-----------|------------|")
        lines.append(f"| **Optimistic** | {estimate.total_optimistic:.1f}h | {estimate.total_optimistic/8:.1f}d | {estimate.total_optimistic/40:.1f}w |")
        lines.append(f"| **Likely** | {estimate.total_likely:.1f}h | {estimate.total_likely/8:.1f}d | {estimate.total_likely/40:.1f}w |")
        lines.append(f"| **Pessimistic** | {estimate.total_pessimistic:.1f}h | {estimate.total_pessimistic/8:.1f}d | {estimate.total_pessimistic/40:.1f}w |")
        lines.append(f"| **Expected (PERT)** | {estimate.total_expected:.1f}h | {estimate.total_expected/8:.1f}d | {estimate.total_expected/40:.1f}w |")
        lines.append("")
        lines.append(f"**95% Confidence Interval:** {estimate.confidence_95_range[0]:.1f}h - {estimate.confidence_95_range[1]:.1f}h")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Component Summary")
        lines.append("")
        lines.append("| Component | Type | Tasks | Optimistic | Likely | Pessimistic | Expected |")
        lines.append("|-----------|------|-------|------------|--------|-------------|----------|")
        for comp in estimate.components:
            comp_opt = sum(t.optimistic_hours for t in comp.tasks)
            comp_like = sum(t.likely_hours for t in comp.tasks)
            comp_pess = sum(t.pessimistic_hours for t in comp.tasks)
            comp_exp = sum(t.expected_hours for t in comp.tasks)
            lines.append(f"| {comp.name} | {comp.type} | {len(comp.tasks)} | {comp_opt:.1f}h | {comp_like:.1f}h | {comp_pess:.1f}h | {comp_exp:.1f}h |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Task-Level Breakdown")
        lines.append("")

        for comp in estimate.components:
            lines.append(f"### {comp.name} ({comp.type.upper()})")
            lines.append("")
            lines.append(comp.description)
            lines.append("")
            if comp.tech_stack:
                lines.append(f"**Tech Stack:** {', '.join(comp.tech_stack)}")
                lines.append("")

            lines.append("**Task-Level PERT Estimates:**")
            lines.append("")
            lines.append("| ID | Task | Opt | Likely | Pess | Expected | SD | 95% CI |")
            lines.append("|----|------|-----|--------|------|----------|----|--------|")
            for task in comp.tasks:
                ci_low, ci_high = task.confidence_95
                lines.append(
                    f"| {task.id} | {task.title} | "
                    f"{task.optimistic_hours:.1f}h | {task.likely_hours:.1f}h | "
                    f"{task.pessimistic_hours:.1f}h | {task.expected_hours:.1f}h | "
                    f"{task.standard_deviation:.1f}h | {ci_low:.1f}-{ci_high:.1f}h |"
                )
            lines.append("")

            comp_opt = sum(t.optimistic_hours for t in comp.tasks)
            comp_like = sum(t.likely_hours for t in comp.tasks)
            comp_pess = sum(t.pessimistic_hours for t in comp.tasks)
            comp_exp = sum(t.expected_hours for t in comp.tasks)
            comp_var = sum(t.standard_deviation ** 2 for t in comp.tasks)
            comp_sd = comp_var ** 0.5
            lines.append(f"**Subtotal:** O={comp_opt:.1f}h | L={comp_like:.1f}h | P={comp_pess:.1f}h | E={comp_exp:.1f}h | SD={comp_sd:.1f}h | 95%=[{comp_exp-2*comp_sd:.1f}h, {comp_exp+2*comp_sd:.1f}h]")
            lines.append("")

            if any(t.risk_factors for t in comp.tasks):
                lines.append("**Risk Factors & Mitigations:**")
                lines.append("")
                for task in comp.tasks:
                    if task.risk_factors:
                        lines.append(f"- **{task.id}: {task.title}**")
                        lines.append(f"  - Risks: {', '.join(task.risk_factors)}")
                        lines.append(f"  - Mitigation: {task.mitigation}")
                        lines.append("")
                lines.append("")

            if comp.tasks and comp.tasks[0].required_skills:
                all_skills = set()
                for t in comp.tasks:
                    all_skills.update(t.required_skills)
                lines.append(f"**Required Skills:** {', '.join(sorted(all_skills))}")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.append("")
        lines.append("## Risk Assessment")
        lines.append("")
        lines.append(estimate.risk_assessment)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Recommended Team")
        lines.append("")
        for role in estimate.recommended_team:
            lines.append(f"- {role}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Critical Path (Top 5)")
        lines.append("")
        for item in estimate.critical_path:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        for assumption in estimate.assumptions:
            lines.append(f"- {assumption}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Exclusions (Out of Scope)")
        lines.append("")
        for exclusion in estimate.exclusions:
            lines.append(f"- {exclusion}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Synapticity Estimation Engine*")

        return "\n".join(lines)
