"""
Project Review Engine — feeds indexed project context to agents and applies modifications.
Single Responsibility: orchestrating review and patch application for external codebases.
"""
import os
import re
from synaptic.utils.project_indexer import ProjectIndexer
from synaptic.core.mission_engine import MissionEngine
from synaptic.core.mission_logger import MissionLogger
from synaptic.core.mission_state import MissionStateManager
from synaptic.config import settings


class ProjectReviewEngine:
    """
    Drives an external project review cycle:
    1. Index the target project
    2. Run the agent team against it
    3. Optionally apply the patch directives back to disk
    """

    def __init__(self):
        self._engine = MissionEngine()
        self._logger = MissionLogger()

    def review(self, project_path: str, goal: str, mission_id: str, apply_changes: bool = False) -> str:
        """
        Runs a structured code review of the project at `project_path`.
        Returns the review report string.
        If `apply_changes` is True, attempts to write suggested file patches back to disk.
        """
        print(f"[REVIEW] Indexing project: {project_path}")
        indexer = ProjectIndexer(project_path)
        context = indexer.build_context()
        files   = indexer.list_files()

        print(f"[REVIEW] {len(files)} files indexed. Dispatching agent team...")

        # --- Review Pass: Product Manager assesses the architecture ---
        arch_review = self._engine.planner.execute(
            f"REVIEW GOAL: {goal}\n\nPROJECT CONTEXT:\n{context}",
            task="Performing Architecture & Quality Review",
            mission_id=mission_id
        )

        # --- Improvement Pass: SWE proposes concrete code changes ---
        improvement = self._engine.coder.execute(
            f"REVIEW GOAL: {goal}\n\nARCHITECTURE REVIEW:\n{arch_review}\n\nPROJECT CONTEXT:\n{context}",
            task="Proposing Concrete Code Improvements",
            mission_id=mission_id
        )

        # --- Security Pass ---
        sec_review = self._engine.auditor.execute(
            f"REVIEW GOAL: {goal}\n\nPROJECT CONTEXT:\n{context}",
            task="Security & Vulnerability Assessment",
            mission_id=mission_id
        )

        # --- Compile full report ---
        report = (
            f"# Synaptic External Project Review\n\n"
            f"**Project:** `{project_path}`\n"
            f"**Goal:** {goal}\n"
            f"**Files Reviewed:** {len(files)}\n\n"
            f"---\n\n"
            f"## Architecture & Quality Review\n\n{arch_review}\n\n"
            f"---\n\n"
            f"## Proposed Improvements\n\n{improvement}\n\n"
            f"---\n\n"
            f"## Security Assessment\n\n{sec_review}\n"
        )

        # --- Persist review log into mission workspace ---
        workspace  = os.path.join(settings.WORKSPACE_PATH, mission_id)
        os.makedirs(workspace, exist_ok=True)
        report_path = os.path.join(workspace, "REVIEW_REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[REVIEW] Full report saved: {report_path}")

        # --- Optional: Apply patches back to target project ---
        if apply_changes:
            self._apply_patches(project_path, improvement)

        return report

    def _apply_patches(self, project_path: str, improvement_output: str) -> None:
        """
        Parses FILE_PATCH blocks from the agent's improvement output and writes them to disk.

        Agents are expected to emit patches in the format:
            FILE_PATCH: relative/path/to/file.py
            ```python
            <full file content>
            ```
        """
        pattern = re.compile(
            r"FILE_PATCH:\s*(.+?)\n```(?:\w+)?\n([\s\S]+?)```",
            re.MULTILINE
        )
        patches = pattern.findall(improvement_output)

        if not patches:
            print("[REVIEW] No FILE_PATCH directives found in agent output. No files modified.")
            return

        for rel_path, new_content in patches:
            rel_path   = rel_path.strip()
            target     = os.path.join(project_path, rel_path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[PATCH] Applied: {rel_path}")

        print(f"[REVIEW] {len(patches)} file(s) patched in: {project_path}")
