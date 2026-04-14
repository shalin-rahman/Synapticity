import asyncio
from .core.mission_engine import MissionEngine
from .core.self_learning import ReflectionEngine

__version__ = "3.2.0"

def launch(mission_id: str, objective: str):
    """Starts a new development project with a defined objective."""
    engine = MissionEngine()
    asyncio.run(engine.run(mission_id, objective))

def resume(mission_id: str):
    """Continues an existing project from its last saved state."""
    engine = MissionEngine()
    asyncio.run(engine.run(mission_id))

def dispatch(mission_id: str, agent_name: str, task: str):
    """Sends a specific specialist to handle an isolated task within a project."""
    engine = MissionEngine()
    asyncio.run(engine.execute_single_agent(mission_id, agent_name, task))

def learn(mission_id: str):
    """Performs a post-project review to capture lessons and update engineering standards."""
    engine = ReflectionEngine()
    asyncio.run(engine.analyze(mission_id))
