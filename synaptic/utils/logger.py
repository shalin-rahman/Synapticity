import logging
import os
import sys
from synaptic.config import settings

import logging.handlers

def get_logger(name: str):
    """
    Creates a logger that saves messages to rotated daily files.
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Try to save logs to daily files
        try:
            os.makedirs("logs", exist_ok=True)
            # Create a new log file every day (when="D") and keep 30 days of history
            fh = logging.handlers.TimedRotatingFileHandler(
                "logs/synaptic.log", 
                when="D", 
                interval=1, 
                backupCount=30,
                encoding='utf-8'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            # Continue without file logging if the folder is not writable
            pass
            
        # Display simplified logs in the terminal
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    
    return logger

# Global instance for quick access
synaptic_log = get_logger("synaptic")
