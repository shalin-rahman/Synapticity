import hashlib
import os

def generate_context_hash(workspace_path: str) -> str:
    """Creates a unique hash for requirement files in a workspace folder."""
    hasher = hashlib.md5()
    found = False
    for root, _, files in os.walk(workspace_path):
        if "output" in root: continue
        for file in sorted(files):
            if file.endswith(('.md', '.pdf', '.txt')):
                try:
                    with open(os.path.join(root, file), "rb") as f:
                        hasher.update(f.read())
                        found = True
                except: pass
    return hasher.hexdigest() if found else None
