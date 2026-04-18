import os
import sys
from datetime import datetime
import uuid
import logging
from typing import Optional

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ServiceCore')

class StructuredLogRecord:
    def __init__(self, level: str, service: str, message: str, component: Optional[str] = None, trace_id: Optional[str] = None):
        self.timestamp = datetime.utcnow().isoformat()
        self.level = level
        self.service = service
        self.message = message
        self.component = component or 'main_entry_point'
        self.trace_id = trace_id or str(uuid.uuid4())

    def to_json(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "message": self.message,
            "component": self.component,
            "trace_id": self.trace_id
        }

class ServiceCore:
    @staticmethod
    def execute(service_name: str) -> str:
        return f"Service {service_name}: Hello, World!"

def main_entry_point():
    service_name = os.getenv('SERVICE_NAME', 'DefaultService')
    
    try:
        # Initialize logging
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        logger.info(f"Initializing {service_name}...")
        
        # Execute core business logic
        service_core = ServiceCore()
        result = service_core.execute(service_name)
        
        # Log successful execution
        log_record = StructuredLogRecord(level='INFO', service=service_name, message=result)
        logger.info(log_record.to_json())
    
    except Exception as e:
        # Log error and exit with non-zero status code
        log_record = StructuredLogRecord(level='ERROR', service=service_name, message=str(e), trace_id=str(uuid.uuid4()))
        logger.error(log_record.to_json())
        sys.exit(1)

if __name__ == "__main__":
    main_entry_point()