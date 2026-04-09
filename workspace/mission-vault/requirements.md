# Mission 001: Secure-Vault Prototype

## Objective
Build a high-security FastAPI micro-vault for storing sensitive encrypted notes.

## Technical Requirements
- **Framework**: FastAPI (Async)
- **Encryption**: Use Advanced Encryption Standard (AES) via the `cryptography` library.
- **Persistence**: Store encrypted notes in a local `vault.json` file.
- **Validation**: Use Pydantic v2 for strict request/response schemas.
- **Master Key**: Implement a master-key derivation using PBKDF2.

## Security Constraints (For On-Call Auditor)
- Zero exposure of raw keys in stdout/logs.
- Protection against path traversal in file persistence.
- Secure handling of cryptographic salts.

## Test Cases (For Tester)
- Verification of successful encryption and decryption cycle.
- Graceful failure when an incorrect master key is provided.
- Validation that note IDs are unique.
