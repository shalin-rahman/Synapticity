"""Integration CLI handlers: deploy, ingest, stress, admin."""
import sys
import getpass
import subprocess
from synaptic.config import settings
from synaptic.cli.utils import console, sanitize_id, require_args


def handle_deploy() -> None:
    if not require_args(3, "Usage: python main.py deploy <mission_id>"):
        return
    from synaptic.utils.git_deployer import GitDeployer
    GitDeployer(sanitize_id(sys.argv[2])).deploy()


def handle_ingest() -> None:
    if not require_args(5, "Usage: python main.py ingest <type: skill|agent> <raw_url> <name>"):
        return
    from synaptic.utils.resource_fetcher import SkillIngestor, AgentIngestor

    ingest_type = sys.argv[2].lower()
    url         = sys.argv[3]
    target_name = sys.argv[4].replace(" ", "-").lower()

    ingestors = {"skill": SkillIngestor, "agent": AgentIngestor}
    if ingest_type not in ingestors:
        console.print(f"[red]Error: Invalid ingestion type '{ingest_type}'. Valid types: skill, agent.[/]")
        return
    ingestors[ingest_type]().fetch(url, target_name)


def handle_stress() -> None:
    subprocess.run([sys.executable, "stress_test.py"])


def handle_admin() -> None:
    password = getpass.getpass("Enter Admin Passcode: ")
    if password == settings.ADMIN_PASSCODE:
        console.print("[bold green][OK] Authentication Successful.[/]")
        console.print("[dim]Admin features unlocked.[/]")
        # Roadmap: Configuration tools for advanced users.
    else:
        console.print("[bold red][FAIL] Authentication Denied.[/]")
