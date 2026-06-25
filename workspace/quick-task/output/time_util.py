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