"""
Project Indexer — crawls a local directory and builds a structured context map.
Single Responsibility: filesystem traversal and file content aggregation.
"""
import os

# Extensions to include in the context snapshot
INDEXABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".cs", ".rb",
    ".php", ".cpp", ".c", ".h", ".rs", ".kt", ".swift",
    ".json", ".yaml", ".yml", ".toml", ".env.example",
    ".md", ".txt", ".html", ".css", ".scss",
    "Dockerfile", "docker-compose.yml", "Makefile",
}

# Directories to always skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".tox", "dist", "build", ".next", ".nuxt", "coverage", ".mypy_cache",
}

MAX_FILE_BYTES = 50_000  # 50 KB cap per file to avoid LLM context overflow


class ProjectIndexer:
    """Recursively walks a project directory and collects readable source content."""

    def __init__(self, project_path: str):
        if not os.path.isdir(project_path):
            raise ValueError(f"Path is not a valid directory: {project_path}")
        self.project_path = os.path.abspath(project_path)

    def build_context(self) -> str:
        """Returns a single aggregated string of all indexed file contents."""
        segments = [f"# Project Index: {self.project_path}\n"]
        file_count = 0

        for root, dirs, files in os.walk(self.project_path):
            # Prune skip directories in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in sorted(files):
                filepath = os.path.join(root, filename)
                ext      = os.path.splitext(filename)[1]

                if ext not in INDEXABLE_EXTENSIONS and filename not in INDEXABLE_EXTENSIONS:
                    continue
                if os.path.getsize(filepath) > MAX_FILE_BYTES:
                    rel = os.path.relpath(filepath, self.project_path)
                    segments.append(f"\n## {rel}\n[FILE TOO LARGE — skipped]\n")
                    continue

                try:
                    relative_path = os.path.relpath(filepath, self.project_path)
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    segments.append(f"\n## {relative_path}\n```{ext.lstrip('.')}\n{content}\n```\n")
                    file_count += 1
                except Exception:
                    pass

        segments.append(f"\n---\n_Total files indexed: {file_count}_\n")
        return "\n".join(segments)

    def list_files(self) -> list[str]:
        """Returns relative paths of all indexable files in the project."""
        result = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in INDEXABLE_EXTENSIONS or f in INDEXABLE_EXTENSIONS:
                    result.append(os.path.relpath(os.path.join(root, f), self.project_path))
        return result
