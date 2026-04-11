"""
Mission workspace — output folder I/O and CI/CD pipeline writing.
Single Responsibility: owns all workspace filesystem writes.
"""
import os
import re


class MissionWorkspace:
    """Handles committing code, docs, and CI/CD configs to the output directory."""

    def __init__(self, mission_path: str):
        self._output = os.path.join(mission_path, "output")
        os.makedirs(self._output, exist_ok=True)

    def commit_code(self, code: str) -> None:
        """Saves generated source code to output/main.py."""
        with open(os.path.join(self._output, "main.py"), "w", encoding="utf-8") as f:
            f.write(code)

    def commit_docs(self, docs: str) -> None:
        """Saves technical documentation to output/TECHNICAL_DOCS.md."""
        if docs:
            with open(os.path.join(self._output, "TECHNICAL_DOCS.md"), "w", encoding="utf-8") as f:
                f.write(docs)

    def commit_pipeline(self, raw_yaml: str) -> None:
        """Extracts and saves a GitHub Actions YAML to the standard workflows path."""
        yaml_block = re.search(r"```yaml\n([\s\S]+?)```", raw_yaml, re.IGNORECASE)
        if yaml_block:
            raw_yaml = yaml_block.group(1)
        elif "```" in raw_yaml:
            raw_yaml = raw_yaml.replace("```", "").strip()

        workflows_dir = os.path.join(self._output, ".github", "workflows")
        os.makedirs(workflows_dir, exist_ok=True)
        with open(os.path.join(workflows_dir, "main.yml"), "w", encoding="utf-8") as f:
            f.write(raw_yaml.strip() + "\n")
