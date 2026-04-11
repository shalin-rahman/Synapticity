import os
from synaptic.config import settings

class SkillRegistry:
    """Manages the discovery and injection of technical skills."""
    
    def __init__(self, path=settings.SKILL_PATH):
        self.path = path
        self._cache = {}  # {skill_id: {"mtime": float, "content": str}}
        self._load_all_skills_quietly()

    def _load_all_skills_quietly(self):
        """Initial baseline index build of skills."""
        if not os.path.exists(self.path): return
        for folder in os.listdir(self.path):
            file_path = os.path.join(self.path, folder, "skill.md")
            if os.path.exists(file_path):
                self._cache_skill(folder, file_path)

    def _cache_skill(self, folder: str, file_path: str):
        try:
            mtime = os.path.getmtime(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                self._cache[folder] = {"mtime": mtime, "content": f.read()}
        except Exception:
            pass

    def _check_hot_reload(self, folder: str, file_path: str):
        """Re-evaluates disk integrity if hot reloading is active. FileSystem watcher logic."""
        if not settings.ENABLE_HOT_RELOAD:
            return
            
        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self._cache.get(folder, {}).get("mtime", 0)
            
            if current_mtime > cached_mtime:
                print(f"[WATCHER] Hot-reloading active skill: {folder}")
                self._cache_skill(folder, file_path)
        except Exception:
            pass

    def inject(self, target_str: str) -> str:
        """Injects relevant skill content if mentioned in the target string."""
        if not os.path.exists(self.path): return ""
        
        injected = ""
        target_normalized = target_str.lower()
        
        # Mapping base keywords to skill folders
        skill_triggers = {
            "test": ["testing-strategies"],
            "qa ": ["testing-strategies"],
            "api": ["api-design"],
            "rest": ["api-design"],
            "db ": ["sqlalchemy-expert", "domain-driven-design"],
            "database": ["sqlalchemy-expert"],
            "secure": ["ai-security-safety", "cryptography-expert", "security-scanner"],
            "security": ["ai-security-safety", "cryptography-expert", "security-scanner"],
            "architecture": ["clean-architecture", "solid-design-patterns"],
            "design": ["solid-design-patterns", "domain-driven-design"],
            "microservice": ["microservices"],
            "agent": ["agentic-architecture", "multi-agent-orchestration"],
            "llm": ["llm-engineering", "data-privacy"],
            "rag": ["rag-implementation"]
        }
        
        # Core skills that should always be injected
        active_skills = {"code-quality-linting"}
        
        # Check folder names directly
        for folder in os.listdir(self.path):
            if folder.replace("-", " ") in target_normalized:
                active_skills.add(folder)
                
        # Check keyword map
        for keyword, skills in skill_triggers.items():
            if keyword in target_normalized:
                active_skills.update(skills)
                
        # Inject the active skills
        for folder in active_skills:
            file_path = os.path.join(self.path, folder, "skill.md")
            if os.path.exists(file_path):
                # Auto-Watch mechanism
                self._check_hot_reload(folder, file_path)
                
                # Fetch entirely from highly-performant RAM Cache
                cached = self._cache.get(folder)
                if cached:
                    print(f"[SKILL] synaptic Skill Injected: {folder}")
                    injected += f"\n\n[SKILL: {folder}]\n{cached['content']}"

        return injected
