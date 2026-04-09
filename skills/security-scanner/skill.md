# Skill: Security Scanner
# Usage: Use periodically to audit code for logic backdoors and security holes.

## Audit Protocol:
- **Injection:** Check for `eval()`, `exec()`, or raw `os.system()` calls with un-sanitized user input.
- **Secrets:** Scan for entropy-based secrets or well-known prefixes (`ghp_`, `sk_`).
- **Data Privacy:** Ensure sensitive data is never logged or returned in error messages.
- **Crypto:** Verify usage of SHA-256 for hashing and AES-GCM for encryption.
- **Logic:** Search for "hidden" admin routes or hardcoded bypasses.

## Success Verdict:
- Final code must follow a "Least Privilege" model.
- All external library imports must be verified for safety.
