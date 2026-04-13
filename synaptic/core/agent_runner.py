import os
from synaptic.config import settings
from synaptic.models.base import AbstractModel
from synaptic.utils.exceptions import ConfigurationError, ModelProviderError
from synaptic.utils.logger import synaptic_log
from synaptic.utils.memory_logger import MemoryLogger
from synaptic.core.analytics import PerformanceAnalytics
import threading
import time
class AgentRunner:
    """
    Manages the communication with specialized agent personas.
    Includes built-in fallback logic if the primary model provider is unavailable.
    """
    
    def __init__(self, model: AbstractModel, persona_file: str, fallback_model: AbstractModel = None):
        self.model = model
        self.persona_file = persona_file
        self.fallback_model = fallback_model
        self._analytics = PerformanceAnalytics()

    def run(self, prompt: str, context: str = "", task: str = "Processing", mission_id: str = None) -> str:
        """Processes a prompt through the chosen persona, using optional context."""
        path = os.path.join(settings.AGENT_PATH, self.persona_file)
        if not os.path.exists(path):
            raise ConfigurationError(
                f"Could not find the persona file: {self.persona_file}. "
                "Ensure the 'agents/' directory is correctly set up."
            )
            
        with open(path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
            
        final_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}" if context else prompt
        
        provider_name = type(self.model).__name__.replace("Adapter", "")
        agent_name = self.persona_file.split('.')[0].upper()
        
        from rich.console import Console
        console = Console()
        
        done_event = threading.Event()
        
        def _heartbeat():
            if settings.HEARTBEAT_INTERVAL <= 0:
                return
            elapsed = 0
            while not done_event.wait(settings.HEARTBEAT_INTERVAL):
                elapsed += settings.HEARTBEAT_INTERVAL
                console.print(f"[dim]  ... {agent_name} is still {task} ({elapsed}s elapsed)[/]")
        
        with console.status(f"[bold cyan]{agent_name}[/] is: [dim]{task}[/] (using {provider_name})..."):
            t = threading.Thread(target=_heartbeat, daemon=True)
            t.start()
            try:
                inf_start = time.time()
                result = self.model.generate(system_instruction, final_prompt)
                inf_duration = time.time() - inf_start
                
                done_event.set()
                self._analytics.log_inference(provider_name, inf_duration)
                MemoryLogger.log_interaction(mission_id, agent_name, task, provider_name, system_instruction, final_prompt, result)
                console.print(f"[bold green][OK][/] {agent_name}: {task} finished ({inf_duration:.2f}s).")
                return result
            except (ModelProviderError, ConfigurationError) as e:
                done_event.set()
                if self.fallback_model:
                    fallback_name = type(self.fallback_model).__name__.replace("Adapter", "")
                    synaptic_log.warning(f"Failover triggered: {e}")
                    
                    console.print(f"\n[bold yellow][WARN][/] {provider_name} was unable to respond. ({e})")
                    console.print(f"[FAILOVER] Switching to [bold cyan]{fallback_name}[/] to continue work...")
                    
                    with console.status(f"[bold cyan]{agent_name}[/] is working: [dim]{task}[/] (via {fallback_name})..."):
                        fallback_done = threading.Event()
                        def _fallback_heartbeat():
                            if settings.HEARTBEAT_INTERVAL <= 0:
                                return
                            elapsed = 0
                            while not fallback_done.wait(settings.HEARTBEAT_INTERVAL):
                                elapsed += settings.HEARTBEAT_INTERVAL
                                console.print(f"[dim]  ... {agent_name} is still {task} ({elapsed}s elapsed via {fallback_name})[/]")
                        
                        fallback_t = threading.Thread(target=_fallback_heartbeat, daemon=True)
                        fallback_t.start()
                        
                        try:
                            result = self.fallback_model.generate(system_instruction, final_prompt)
                            fallback_done.set()
                            MemoryLogger.log_interaction(mission_id, agent_name, task, fallback_name, system_instruction, final_prompt, result)
                            console.print(f"[DONE] [green]{agent_name} check-in:[/] [dim]{task} complete.[/]")
                            return result
                        except Exception as inner_e:
                            fallback_done.set()
                            raise inner_e
                else:
                    raise e
