import os
from synaptic.config import settings
from synaptic.models.base import AbstractModel
from synaptic.utils.exceptions import ConfigurationError

class AgentRunner:
    """Handles the execution of specific agent personas."""
    
    def __init__(self, model: AbstractModel, persona_file: str):
        self.model = model
        self.persona_file = persona_file

    def execute(self, prompt: str, context: str = "") -> str:
        """Runs the loaded persona against a prompt and optional context."""
        path = os.path.join(settings.AGENT_PATH, self.persona_file)
        if not os.path.exists(path):
            raise ConfigurationError(
                f"Critical synaptic Persona File missing: {self.persona_file}. "
                "Please ensure the 'agents/' directory is correctly populated."
            )
            
        with open(path, "r") as f:
            system_instruction = f.read()
            
        final_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}" if context else prompt
        return self.model.generate(system_instruction, final_prompt)
