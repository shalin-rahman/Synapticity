# Overview

This guide explains how to set up a simple "Hello, World!" Python script that meets the specified requirements. The script initializes logging, executes core business logic, and handles errors gracefully.

# Setup

To run this script, you need:

1. **Python 3.x**: Ensure Python is installed on your system.
2. **A text editor**: Use any text editor to create and save the script file.

# How it Works

The script consists of three main parts:

1. **`main_entry_point` Module**: This module initializes logging and calls the core business logic.
2. **`ServiceCore` Class**: Encapsulates the "Hello, World!" function.
3. **Logging Subsystem**: Uses Python's `logging` module for structured output.

# Security

The script ensures that all output is logged in a structured JSON format to facilitate centralized logging platforms like ELK stack or Splunk. No sensitive data is handled.

---

## Detailed Steps

### Step 1: Create the Script File

Create a new file named `hello_world.py` and paste the following code into it:

```python
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
```

### Step 2: Run the Script

Open a terminal and navigate to the directory containing `hello_world.py`. Run the script using Python:

```sh
python hello_world.py
```

You should see output similar to this in your terminal:

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS.mmmZ",
  "level": "INFO",
  "service": "DefaultService",
  "message": "Service DefaultService: Hello, World!",
  "component": "main_entry_point",
  "trace_id": "UUID_Placeholder"
}
```

### Step 3: Test with Environment Variable

To test the script with an environment variable, set `SERVICE_NAME` and run the script again:

```sh
export SERVICE_NAME=AuthService
python hello_world.py
```

You should see output similar to this:

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS.mmmZ",
  "level": "INFO",
  "service": "AuthService",
  "message": "Service AuthService: Hello, World!",
  "component": "main_entry_point",
  "trace_id": "UUID_Placeholder"
}
```

### Step 4: Test Error Handling

To test error handling, introduce a simulated failure by raising an exception:

```python
class ServiceCore:
    @staticmethod
    def execute(service_name: str) -> str:
        raise ZeroDivisionError("Simulated error")
```

Run the script again:

```sh
python hello_world.py
```

You should see output similar to this in your terminal:

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS.mmmZ",
  "level": "ERROR",
  "service": "DefaultService",
  "message": "Simulated error",
  "component": "main_entry_point",
  "trace_id": "UUID_Placeholder"
}
```

And the script should exit with a non-zero status code.

---

This guide provides a simple, direct approach to setting up and running a Python script that meets the specified requirements.