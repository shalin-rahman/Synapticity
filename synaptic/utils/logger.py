import logging
import os
import sys
from synaptic.config import settings

def get_logger(name: str):
    """
    Returns a resilient logger. 
    Falls back to StreamHandler (Console) if FileSystem is locked/read-only.
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    if not logger.handlers:
        # Final formatting
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # [SHIELD] Attempt File Handling
        try:
            os.makedirs("logs", exist_ok=True)
            fh = logging.FileHandler("logs/synaptic.log", encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            # Fallback to console only if file system fails
            pass
            
        # Standard Console Summary
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    
    return logger

# Global instance for quick access
synaptic_log = get_logger("synaptic")
