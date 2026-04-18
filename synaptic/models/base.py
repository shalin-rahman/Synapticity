from abc import ABC, abstractmethod

class AbstractModel(ABC):
    """Base interface for all synaptic LLM adapters."""
    
    @abstractmethod
    async def generate(self, system_instruction: str, prompt: str) -> str:
        """Process a request and return the model's response."""
        pass
