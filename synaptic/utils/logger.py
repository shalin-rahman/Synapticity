import logging
import os
from synaptic.config import settings

def get_logger(name: str):
    """Returns a configured logger for the synaptic framework."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        # File Handler (Audit Log)
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler("logs/synaptic.log")
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        
        # Console Handler (Summary)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        # We only want INFO+ on console to avoid cluttering the CLI
        ch.setLevel(logging.INFO)
        # Note: In a production CLI, you might suppress this for rich output
    
    return logger

# Global instance for quick access
synaptic_log = get_logger("synaptic")
