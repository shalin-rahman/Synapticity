import os
from synaptic.config import settings

class SkillRegistry:
    """Manages the discovery and injection of technical skills from local and external directories."""
    
    def __init__(self, path=settings.SKILL_PATH, external_paths=None):
        self.path = path
        self.external_paths = external_paths or settings.EXTERNAL_SKILL_PATHS
        self._cache = {}  # {skill_id: {"mtime": float, "content": str, "source_dir": str}}
        self._load_all_skills_quietly()

    def _load_all_skills_quietly(self):
        """Initial baseline index build of skills from local and external directories."""
        # Load local skills first
        if os.path.exists(self.path):
            self._load_from_directory(self.path, is_external=False)
        
        # Load external skills after (they override local skills on conflict)
        if self.external_paths:
            for ext_path in self.external_paths:
                if isinstance(ext_path, str) and os.path.exists(ext_path):
                    self._load_from_directory(ext_path, is_external=True)
                elif isinstance(ext_path, str):
                    print(f"[WARNING] External skill path not found: {ext_path}")

    def _load_from_directory(self, directory: str, is_external: bool = False):
        """Load all skills from a specific directory (case-insensitive skill.md lookup)."""
        source_label = "external" if is_external else "local"
        try:
            for folder in os.listdir(directory):
                folder_path = os.path.join(directory, folder)
                if not os.path.isdir(folder_path):
                    continue
                # Accept skill.md or SKILL.md (external repos may use uppercase)
                file_path = None
                for candidate in ("skill.md", "SKILL.md"):
                    p = os.path.join(folder_path, candidate)
                    if os.path.exists(p):
                        file_path = p
                        break
                if file_path:
                    self._cache_skill(folder, file_path, source_dir=directory, source_label=source_label)
        except Exception as e:
            print(f"[WARNING] Error loading {source_label} skills from {directory}: {e}")

    def _cache_skill(self, folder: str, file_path: str, source_dir: str = "", source_label: str = "local"):
        try:
            mtime = os.path.getmtime(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                self._cache[folder] = {
                    "mtime": mtime, 
                    "content": f.read(),
                    "source_dir": source_dir,
                    "source_label": source_label
                }
        except Exception as e:
            print(f"[WARNING] Error caching skill {folder}: {e}")

    def _check_hot_reload(self, folder: str, file_path: str):
        """Re-evaluates disk integrity if hot reloading is active. FileSystem watcher logic."""
        if not settings.ENABLE_HOT_RELOAD:
            return
            
        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self._cache.get(folder, {}).get("mtime", 0)
            
            if current_mtime > cached_mtime:
                # Determine if skill is from external or local directory
                cached_item = self._cache.get(folder, {})
                source_dir = cached_item.get("source_dir", "")
                is_external = any(source_dir.startswith(ext_path) for ext_path in (self.external_paths or []) if isinstance(ext_path, str))
                source_label = "external" if is_external else "local"
                
                print(f"[WATCHER] Hot-reloading {source_label} skill: {folder}")
                self._cache_skill(folder, file_path, source_dir=source_dir, source_label=source_label)
        except Exception as e:
            print(f"[WARNING] Error during hot reload check for {folder}: {e}")

    def inject(self, target_str: str) -> str:
        """Injects relevant skill content if mentioned in the target string."""
        # Check if any skill directories exist
        local_exists = os.path.exists(self.path)
        external_exists = any(
            isinstance(p, str) and os.path.exists(p) 
            for p in (self.external_paths or [])
        )
        if not local_exists and not external_exists:
            return ""
        
        injected = ""
        target_normalized = target_str.lower()
        
        # Mapping base keywords to skill folders (Foundational Smart Thinking)
        skill_triggers = {
            "test": ["testing-strategies", "shift-left-testing", "test-driven-development"],
            "tdd": ["test-driven-development", "testing-strategies"],
            "qa ": ["testing-strategies", "shift-left-testing"],
            "api": ["api-design", "agile-product-management", "api-and-interface-design"],
            "rest": ["api-design", "api-and-interface-design"],
            "openapi": ["api-and-interface-design"],
            "db ": ["sqlalchemy-expert", "domain-driven-design"],
            "database": ["sqlalchemy-expert"],
            "sql": ["sqlalchemy-expert"],
            "mysql": ["sqlalchemy-expert", "domain-driven-design"],
            "postgres": ["sqlalchemy-expert", "domain-driven-design"],
            "secure": ["ai-security-safety", "cryptography-expert", "security-scanner", "devsecops-hardening", "security-and-hardening"],
            "security": ["ai-security-safety", "cryptography-expert", "security-scanner", "devsecops-hardening", "security-and-hardening"],
            "architecture": ["clean-architecture", "solid-design-patterns", "zero-defect-engineering"],
            "design": ["solid-design-patterns", "domain-driven-design", "zero-defect-engineering"],
            "plan": ["agile-product-management", "planning-and-task-breakdown"],
            "goal": ["agile-product-management"],
            "task": ["planning-and-task-breakdown"],
            "doc": ["technical-writing-standards", "documentation-and-adrs"],
            "write": ["technical-writing-standards"],
            "adr": ["documentation-and-adrs"],
            "microservice": ["microservices"],
            "debug": ["debugging-and-error-recovery"],
            "error": ["debugging-and-error-recovery"],
            "fix": ["debugging-and-error-recovery"],
            "review": ["code-review-and-quality"],
            "refactor": ["code-simplification", "code-review-and-quality"],
            "simplif": ["code-simplification"],
            "performance": ["performance-optimization"],
            "optim": ["performance-optimization"],
            "frontend": ["frontend-ui-engineering"],
            "ui": ["frontend-ui-engineering"],
            "react": ["frontend-ui-engineering"],
            "git": ["git-workflow-and-versioning"],
            "branch": ["git-workflow-and-versioning"],
            "deploy": ["ci-cd-and-automation", "devops-cicd"],
            "ci": ["ci-cd-and-automation", "devops-cicd"],
            "cd": ["ci-cd-and-automation"],
            "docker": ["python-docker", "ci-cd-and-automation"],
            "container": ["python-docker"],
            "migrat": ["deprecation-and-migration"],
            "deprecat": ["deprecation-and-migration"],
            "ship": ["shipping-and-launch"],
            "launch": ["shipping-and-launch"],
            "spec": ["spec-driven-development"],
            "agent": ["agentic-architecture", "multi-agent-orchestration"],
            "llm": ["llm-engineering", "data-privacy"],
            "rag": ["rag-implementation"],
            "estimate": ["estimation-engineering", "agile-product-management"],
            "estimation": ["estimation-engineering", "agile-product-management"],
            "async": ["python-asyncio"],
            "asyncio": ["python-asyncio"],
            "concurrent": ["python-asyncio"],
            "pydantic": ["pydantic-v2"],
            "settings": ["pydantic-v2"],
            "basemodel": ["pydantic-v2"],
            "postgres": ["postgres-performance", "sqlalchemy-expert"],
            "pgvector": ["postgres-performance"],
            "git ": ["git-workflow"],
            "commit": ["git-workflow"],
            "pull request": ["git-workflow"],
        }
        
        # Core foundational skills that should ALWAYS be injected for every mission
        active_skills = {
            "code-quality-linting", 
            "autonomous-lessons",
            "zero-defect-engineering",
            "devsecops-hardening"
        }
        
        # Match skill names against target using the already-built cache (no disk re-scan)
        for folder in self._cache:
            if folder.replace("-", " ") in target_normalized:
                active_skills.add(folder)
                
        # Check keyword map
        for keyword, skills in skill_triggers.items():
            if keyword in target_normalized:
                active_skills.update(skills)
                
        # Inject the active skills (from cache, which prioritizes external over local)
        for folder in active_skills:
            # Try external paths first (they have priority), accept skill.md or SKILL.md
            file_path = None
            for ext_path in (self.external_paths or []):
                if isinstance(ext_path, str):
                    for fname in ("skill.md", "SKILL.md"):
                        candidate = os.path.join(ext_path, folder, fname)
                        if os.path.exists(candidate):
                            file_path = candidate
                            break
                if file_path:
                    break

            # Fall back to local path
            if not file_path:
                for fname in ("skill.md", "SKILL.md"):
                    candidate = os.path.join(self.path, folder, fname)
                    if os.path.exists(candidate):
                        file_path = candidate
                        break
            
            if file_path:
                # Auto-Watch mechanism
                self._check_hot_reload(folder, file_path)
                
                # Fetch entirely from highly-performant RAM Cache
                cached = self._cache.get(folder)
                if cached:
                    source_label = cached.get("source_label", "local")
                    print(f"[SKILL] synaptic Skill Injected ({source_label}): {folder}")
                    injected += f"\n\n[SKILL: {folder}]\n{cached['content']}"

        return injected
