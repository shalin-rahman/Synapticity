"""
Core Logic Layer: Base64 Utility Service.

This module encapsulates all business logic for Base64 encoding and decoding.
It is designed to be completely agnostic of the CLI framework, making it
highly testable and reusable (NFR-3.1).

Adheres to the Single Responsibility Principle (SRP) by having only
one reason to change: the Base64 algorithm itself.
"""

import base64
from typing import Union

class Base64DecodeError(Exception):
    """
    Custom exception raised when Base64 decoding fails due to malformed input.

    This provides a controlled, catchable exception type for the calling
    application layer, decoupling it from the underlying 'binascii' library.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def encode(data: Union[bytes, str]) -> str:
    """
    Encodes raw data (bytes or string) into a standard Base64 string.

    Args:
        data: The raw data to encode. If a string, it is implicitly
              encoded to UTF-8 bytes.

    Returns:
        The Base64 encoded string representation.

    Raises:
        TypeError: If the input data type is unsupported.
    """
    if isinstance(data, str):
        # Treat string input as UTF-8 bytes for consistent processing
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        raise TypeError("Input data must be bytes or str.")

    # Use standard base64 encoding
    encoded_bytes = base64.b64encode(data_bytes)
    return encoded_bytes.decode('ascii')


def decode(encoded_data: str) -> bytes:
    """
    Decodes a standard Base64 string back into its original raw bytes.

    Args:
        encoded_data: The Base64 encoded string.

    Returns:
        The original raw bytes.

    Raises:
        Base64DecodeError: If the input string is not valid Base64
                            (e.g., incorrect padding, invalid characters).
    """
    try:
        # Base64 decoding expects bytes, so we encode the input string first.
        encoded_bytes = encoded_data.encode('ascii')
        decoded_bytes = base64.b64decode(encoded_bytes)
        return decoded_bytes
    except base64.binascii.Error as e:
        # CRITICAL FIX: Catch the underlying binascii error but raise the
        # specified custom Base64DecodeError to maintain a clean API contract.
        raise Base64DecodeError(
            f"Decoding failed: Invalid Base64 input provided. Details: {e}"
        )

# Note: The standard library 'base64' module is required for this module to function.