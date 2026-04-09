from .core.workflow import MissionEngine

__version__ = "2.0.0"

def launch(mission_id: str, objective: str):
    """Main entry for the The State of Intelligent Connection."""
    engine = MissionEngine()
    engine.execute_mission(mission_id, objective)

def resume(mission_id: str):
    """Resumes a hibernated synaptic mission from its last checkpoint."""
    engine = MissionEngine()
    engine.execute_mission(mission_id)
