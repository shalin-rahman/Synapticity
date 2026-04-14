import os
import datetime
import threading
import time
from synaptic.config import settings
from synaptic.models.base import AbstractModel
from synaptic.utils.exceptions import ConfigurationError, ModelProviderError
from synaptic.utils.logger import synaptic_log
from synaptic.utils.memory_logger import MemoryLogger
from synaptic.core.analytics import PerformanceAnalytics

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
            raise ConfigurationError(f"Persona file missing: {self.persona_file}")
            
        with open(path, "r", encoding="utf-8") as f:
            system = f.read()
            
        final_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}" if context else prompt
        agent_name   = self.persona_file.split('.')[0].upper()
        
        try:
            return self._dispatch_with_monitoring(
                self.model, system, final_prompt, task, agent_name, mission_id
            )
        except (ModelProviderError, ConfigurationError) as e:
            if self.fallback_model:
                fallback_name = type(self.fallback_model).__name__.replace("Adapter", "")
                synaptic_log.warning(f"Failover triggered for {agent_name}: {e}")
                
                from rich.console import Console
                Console().print(f"\n[bold yellow][WARN][/] {self._get_model_identity(self.model)} failed. Switching to {fallback_name}...")
                
                return self._dispatch_with_monitoring(
                    self.fallback_model, system, final_prompt, task, agent_name, mission_id, is_fallback=True
                )
            raise

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _dispatch_with_monitoring(self, model_adapter, system, prompt, task, agent_name, mission_id, is_fallback=False) -> str:
        """Executes a model call while maintaining a live CLI progress monitor."""
        from rich.console import Console
        console = Console()
        
        provider_name = type(model_adapter).__name__.replace("Adapter", "")
        model_name    = self._get_model_identity(model_adapter)
        display_label = f"{provider_name} {model_name}"
        suffix        = " (FALLBACK)" if is_fallback else ""
        
        # Capture precise start time
        start_dt = datetime.datetime.now().strftime("%H:%M:%S")

        # Static starting message to ground the user (includes timestamp)
        console.print(f"[{start_dt}] [bold cyan]{agent_name}[/] started: [dim]{task}[/] (via {display_label}){suffix}")

        done_event = threading.Event()
        
        monitor_thread = threading.Thread(
            target=self._run_progress_monitor, 
            args=(done_event, agent_name, task, suffix), 
            daemon=True
        )
        monitor_thread.start()
        
        try:
            start_time = time.time()
            result = model_adapter.generate(system, prompt)
            duration = time.time() - start_time
            
            done_event.set()
            self._analytics.log_inference(provider_name, duration)
            MemoryLogger.log_interaction(mission_id, agent_name, task, provider_name, system, prompt, result)
            
            console.print(f"[bold green][OK][/] {agent_name}: {task} finished ({duration:.2f}s).")
            return result
        except Exception:
            done_event.set()
            raise

    def _run_progress_monitor(self, stop_event: threading.Event, agent_name: str, task: str, suffix: str):
        """Prints periodic 'still working' updates to the CLI."""
        if settings.HEARTBEAT_INTERVAL <= 0:
            return
            
        from rich.console import Console
        console = Console()
        elapsed = 0
        while not stop_event.wait(settings.HEARTBEAT_INTERVAL):
            elapsed += settings.HEARTBEAT_INTERVAL
            console.print(f"[dim]  ... {agent_name} is still {task}{suffix} ({elapsed}s elapsed)[/]")

    def _get_model_identity(self, adapter) -> str:
        """Extracts the semantic name of the model from the adapter."""
        name = type(adapter).__name__
        if "Ollama" in name: return settings.OLLAMA_MODEL
        if "Gemini" in name: return settings.GEMINI_MODEL
        if "Claude" in name: return settings.CLAUDE_MODEL
        return "Unknown"
