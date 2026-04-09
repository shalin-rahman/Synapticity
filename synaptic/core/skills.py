import os
from synaptic.config import settings

class SkillRegistry:
    """Manages the discovery and injection of technical skills."""
    
    def __init__(self, path=settings.SKILL_PATH):
        self.path = path

    def inject(self, target_str: str) -> str:
        """Injects relevant skill content if mentioned in the target string."""
        if not os.path.exists(self.path): return ""
        
        injected = ""
        for folder in os.listdir(self.path):
            file_path = os.path.join(self.path, folder, "skill.md")
            if os.path.exists(file_path):
                # Match normalized folder name
                if folder.lower().replace("-", " ") in target_str.lower():
                    print(f"💉 synaptic Skill Injected: {folder}")
                    with open(file_path, "r") as f:
                        injected += f"\n\n[SKILL: {folder}]\n{f.read()}"
        return injected
