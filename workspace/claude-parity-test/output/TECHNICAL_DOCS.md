# TECHNICAL_DOCS.md

# Base64 Utility CLI: Source of Truth Documentation

**Version:** 1.0.0
**Date:** 2023-10-27
**Author:** Lead Technical Architect
**Status:** Production Ready

## 🚀 Overview

The Base64 Utility CLI is a robust, modular command-line tool designed to reliably encode and decode arbitrary binary data using the standard Base64 scheme.

This utility adheres strictly to the **Separation of Concerns (SoC)** principle. All core business logic (encoding/decoding algorithms) is isolated within `core.py`, ensuring that the module is entirely unit-testable and agnostic to the CLI framework. The `main.py` module handles the presentation layer, argument parsing, and I/O management.

**Value Proposition:** Provides a high-performance, maintainable, and extensible utility for data transformation, minimizing the risk of coupling business logic to CLI implementation details.

---

## 🏗️ Architecture Diagram

The system follows a clear three-tier architecture: Presentation $\rightarrow$ Service $\rightarrow$ Utility.

```mermaid
graph TD
    A[User Input / STDIN] -->|Data Stream| B(main.py: CLI Entry Point);
    B -->|1. Data Extraction & Validation| C{Input Data (bytes/str)};
    C -->|2. Call Core Service| D[core.py: Base64 Service Layer];
    D -->|3. Processed Data (bytes/str)| C;
    C -->|4. Output Formatting| B;
    B -->|Output Stream| E[STDOUT / Output File];

    subgraph Core Logic Layer
        D
    end

    subgraph Presentation Layer
        B
    end

    subgraph Utility Layer
        A
        E
    end
```

**Data Flow Rationale:**
1.  `main.py` intercepts the input (from STDIN, file, or argument).
2.  It sanitizes and passes the raw bytes/string to `core.py`.
3.  `core.py` executes the pure algorithm and returns the result.
4.  `main.py` handles the final output redirection (STDOUT or specified file).

---

## ⚙️ Installation & Prerequisites

### Prerequisites
*   Python 3.8+
*   Standard Python libraries (No external dependencies required, adhering to NFR-2.2).

### Setup Instructions
1.  **Clone Repository:**
    ```bash
    git clone <repository-url>
    cd base64-utility
    ```
2.  **Execution:** The utility is executed directly via the `main.py` entry point.
    ```bash
    python main.py --help
    ```

---

## 🧩 Core Component Documentation

### 1. `core.py` (Base64 Utility Service)

**Responsibility:** Encapsulates all Base64 encoding and decoding algorithms. This module is the **Source of Truth** for the Base64 logic.
**Design Pattern:** Service Class/Module.
**Testability:** High. Can be imported and tested independently of `main.py`.

#### Custom Exception
*   **`Base64DecodeError(Exception)`:**
    *   **Purpose:** Provides a controlled, catchable exception for decoding failures, abstracting the underlying `binascii.Error`.
    *   **Usage:** Must be caught by the calling layer (`main.py`) to provide user-friendly error messages.

#### API Reference

##### `encode(data: Union[bytes, str]) -> str`
| Parameter | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `data` | `bytes` or `str` | The raw data to encode. If `str`, it is treated as UTF-8. | Must be a string or bytes object. |
| **Returns** | `str` | The standard Base64 encoded string. | Always a printable ASCII string. |
| **Raises** | `TypeError` | If the input data type is unsupported. | |

**Example Usage (Unit Test):**
```python
# Test AC-1.1
encoded = core.encode(b'\xde\xad\xbe\xef')
# Result: "3q2+7w=="
```

##### `decode(encoded_data: str) -> bytes`
| Parameter | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `encoded_data` | `str` | The Base64 encoded string. | Must contain only valid Base64 characters (A-Z, a-z, 0-9, +, /, =). |
| **Returns** | `bytes` | The original raw bytes. | |
| **Raises** | `Base64DecodeError` | If the input string is malformed (e.g., incorrect padding, invalid characters). | |

**Example Usage (Unit Test):**
```python
# Test AC-1.2
decoded = core.decode("3q2+7w==")
# Result: b'\xde\xad\xbe\xef'

# Test AC-1.3 (Failure Handling)
try:
    core.decode("INVALID_BASE64")
except core.Base64DecodeError as e:
    print(f"Caught expected error: {e}")
```

***

### 2. `main.py` (CLI Entry Point)

**Responsibility:** Handles argument parsing, I/O management, and orchestrates the call to `core.py`.
**Design Pattern:** CLI Entry Point.
**Interaction:** Reads from STDIN/File $\rightarrow$ Calls `core.encode`/`core.decode` $\rightarrow$ Writes to STDOUT/File.

#### API Reference (CLI Arguments)

| Argument | Type | Required | Description | Usage Example |
| :--- | :--- | :--- | :--- | :--- |
| `command` | Subcommand | Yes | Must be `encode` or `decode`. | `utility encode` |
| `-i`, `--input` | Path/File | No | Path to the input file. If omitted, STDIN is used. | `utility encode -i data.txt` |
| `-o`, `--output` | Path/File | No | Path to redirect the resulting data. If omitted, STDOUT is used. | `utility decode -o result.bin` |
| `--raw` | Flag | No | Forces the output to be raw bytes (useful for piping to other binary tools). | `utility encode --raw` |

**Execution Flow Logic:**
1.  **Input Determination:** Checks for `-i` file path. If not present, checks if STDIN is available. If neither, raises an error.
2.  **Data Acquisition:** Reads content from the determined source into a single `bytes` object.
3.  **Execution:** Calls the appropriate function in `core.py` (`encode` or `decode`).
4.  **Output Handling:**
    *   If `-o` is provided, writes the result to the file path.
    *   Otherwise, writes the result to STDOUT.
    *   If `--raw` is provided, the output stream is configured for binary writing.

---

## 🛡️ Security & Performance Considerations

### Security (NFR-2)
*   **Input Sanitization:** All input data is immediately converted to `bytes` before being