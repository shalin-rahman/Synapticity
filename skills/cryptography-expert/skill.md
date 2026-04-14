# Skill: Cryptography Expert (Principal Level)
# Usage: Use for secure data persistence, encrypted vaults, and sensitive key management.

## 🛡️ Mandatory Standards:
- **AES-256-GCM**: Always prefer Authenticated Encryption (GCM mode) over CBC to prevent padding oracle attacks and ensure data integrity.
- **Argon2 / PBKDF2**: Use professional-grade key derivation for password-based keys. Never use raw SHA-256 for passwords.
- **Cryptographically Secure PRNG**: Always use `secrets` or `os.urandom` for salts, nonces, and IVs. Never use the `random` module.
- **Zero-Persistence**: Ensure unencrypted data exists only in memory for the shortest possible duration. Clear buffers when done.
- **Standard Libraries**: Prefer `cryptography.io` (Python's leading library) over custom implementations.

## 🛠️ Secure Implementation (AES-GCM):
```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_vault_data(data: bytes, key: bytes) -> bytes:
    """Encrypts data using AES-256-GCM."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # NIST standard for GCM
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext

def decrypt_vault_data(combined_data: bytes, key: bytes) -> bytes:
    """Decrypts data and verifies integrity."""
    nonce = combined_data[:12]
    ciphertext = combined_data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
```

## ⚠️ Security Anti-Patterns:
- Hardcoded IVs or nonces.
- Storing keys in the same database as the encrypted data.
- Using ECB mode (electronic codebook) which leaks patterns.
- Reusing nonces with the same key.
