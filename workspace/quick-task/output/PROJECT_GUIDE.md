# FILE: time_util.py

```python
"""
Module to provide utility functions for handling time-related operations.
"""

import datetime

def get_current_time() -> str:
    """
    Returns the current time in the format YYYY-MM-DD HH:MM:SS.

    Returns:
        str: The current time as a string in the specified format.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Example usage
if __name__ == "__main__":
    print(get_current_time())
```

### Overview
This script, `time_util.py`, is a simple Python utility that prints the current system time in a readable format. It uses Python's built-in `datetime` module to achieve this.

### Setup
1. Save the code above into a file named `time_util.py`.
2. Open your terminal or command prompt.
3. Navigate to the directory where you saved `time_util.py`.

### How it Works
The script defines a function `get_current_time()` that:
- Imports the `datetime` module.
- Uses `datetime.datetime.now()` to get the current date and time.
- Formats this datetime object into a string using `strftime("%Y-%m-%d %H:%M:%S")`.

When you run the script, it will print the current time in the format `YYYY-MM-DD HH:MM:SS`.

### Security
This script uses only standard Python libraries, which are generally safe and well-maintained. There is no external dependency or sensitive data handling, so security concerns are minimal.

To use this script:
1. Open your terminal.
2. Navigate to the directory containing `time_util.py`.
3. Run the script by typing `python time_util.py` and pressing Enter.

You should see the current system time printed in the specified format.