# Skill: Data Privacy & LLM Compliance
# Usage: Use when building AI systems that process Personal Identifiable Information (PII) or sensitive enterprise data.

## 🔒 The Principle of Data Minimization
- **Context is Liability**: Only send the absolute minimum amount of data required to solve the task into the LLM's context window. 
- If an agent is deciding whether to approve a transaction, it needs the transaction amount and user tier, not the user's social security number or physical home address.

## 🎭 PII Masking & Tokenization
- Implement a robust scrubbing layer *before* the prompt hits the API.
- Use regex or Named Entity Recognition (NER) models (like Presidio) to detect and mask Emails, Phone Numbers, Names, and API Keys.
- Route: `User Data -> Scrubbing Engine -> [ANONYMIZED_CONTEXT] -> LLM API -> De-Scrubbing Engine -> User`.

## 🏛️ Enterprise Compliance
- **Data Residency**: Understand where the LLM API is physically hosted. If the user is in the EU, ensure the API endpoint complies with GDPR data residency rules.
- **Zero Data Retention**: When using external APIs (like OpenAI or Gemini), ensure "Zero Data Retention" (ZDR) agreements are active, meaning the provider will not log your API payloads or use them for training future models.

## 🚫 Privacy Anti-Patterns
- Using standard ChatGPT web interfaces for proprietary code or customer data. Always use the enterprise API with ZDR configured.
- Reversing hashes or "weakly" anonymizing data (like switching names but keeping highly specific geographic and demographic markers that allow de-anonymization).
