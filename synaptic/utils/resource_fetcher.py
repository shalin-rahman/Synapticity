import os
import re
import requests
from abc import ABC, abstractmethod
from synaptic.config import settings
from rich.console import Console

console = Console()

class RemoteResourceFetcher(ABC):
    """
    Abstract Base Class for ingesting remote architectural assets.
    Enforces DRY and SOLID principles for network operations.
    """

    def _convert_github_url_to_raw(self, url: str) -> str:
        """Converts a standard GitHub web URL into a raw user content URL."""
        if "github.com" in url and "blob" in url:
            return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        return url

    @abstractmethod
    def _normalize_content(self, name: str, raw_content: str) -> str:
        """Subclasses must implement their own contextual normalization logic."""
        pass

    @abstractmethod
    def _save_content(self, name: str, content: str):
        """Subclasses define where and how to persist the resource."""
        pass

    def fetch(self, url: str, name: str) -> bool:
        """Generic template method connecting, validating, formatting, and saving."""
        console.print(f"[{'bold cyan'}FETCH{'/bold cyan'}] Retrieving '{name}' from: {url}")
        
        raw_url = self._convert_github_url_to_raw(url)
        
        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
            content = response.text
            
            if not content.strip():
                console.print(f"[{'bold red'}ERROR{'/bold red'}] Fetched payload is empty.")
                return False

            normalized = self._normalize_content(name, content)
            self._save_content(name, normalized)
            
            console.print(f"[{'bold green'}SUCCESS{'/bold green'}] Resource '{name}' ingested successfully.")
            return True

        except requests.exceptions.RequestException as e:
            console.print(f"[{'bold red'}FAIL{'/bold red'}] Network error during ingestion: {e}")
            return False

class SkillIngestor(RemoteResourceFetcher):
    """Concrete implementation for sourcing Playbooks and Skills."""
    
    def _normalize_content(self, name: str, raw_content: str) -> str:
        header = f"# Synaptic Expert Playbook: {name.replace('-', ' ').title()}\n"
        header += "> Extracted and Normalized via Synaptic Ingestion Engine\n\n---\n\n"
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_content)
        return header + cleaned

    def _save_content(self, name: str, content: str):
        target_dir = os.path.join(settings.SKILL_PATH, name)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, "skill.md")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

class AgentIngestor(RemoteResourceFetcher):
    """Concrete implementation for sourcing custom Agent Personas."""

    def _normalize_content(self, name: str, raw_content: str) -> str:
        # Agents require strict system instructions, but no heavy markdown normalization.
        # We ensure it ends cleanly.
        header = f"--- ROLE INGESTION: {name.upper()} ---\n"
        cleaned = raw_content.strip() + "\n"
        return header + cleaned

    def _save_content(self, name: str, content: str):
        os.makedirs(settings.AGENT_PATH, exist_ok=True)
        # Agent personas are mapped as single markdown files directly inside agents/
        target_file = os.path.join(settings.AGENT_PATH, f"{name}.md")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
