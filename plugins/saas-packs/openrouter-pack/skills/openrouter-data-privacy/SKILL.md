---
name: openrouter-data-privacy
description: |
  Understand OpenRouter data privacy. Triggers on "openrouter privacy",
  "openrouter data", "openrouter GDPR", "openrouter data retention".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Data Privacy

## OpenRouter Data Handling

### What OpenRouter Stores
```
OpenRouter may store:
- Request metadata (timestamps, models used)
- API key usage statistics
- Billing information

OpenRouter privacy policy:
- Check openrouter.ai/privacy for current policy
- Requests routed to providers follow their policies
```

### Provider Data Policies
```
Each model provider has different policies:

OpenAI:
- API data not used for training (by default)
- 30-day retention for abuse monitoring
- Zero Data Retention available

Anthropic:
- API data not used for training
- Short-term retention for safety

Open Source (via inference providers):
- Varies by hosting provider
- Check specific provider policies
```

## PII Protection

### Redacting Sensitive Data
```python
import re

class PIIRedactor:
    """Redact PII before sending to API."""

    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }

    def __init__(self, patterns: dict = None):
        self.patterns = patterns or self.PATTERNS

    def redact(self, text: str) -> tuple[str, dict]:
        """Redact PII and return mapping for restoration."""
        redacted = text
        mapping = {}
        counter = 0

        for pii_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, redacted):
                original = match.group()
                placeholder = f"[REDACTED_{pii_type.upper()}_{counter}]"
                mapping[placeholder] = original
                redacted = redacted.replace(original, placeholder, 1)
                counter += 1

        return redacted, mapping

    def restore(self, text: str, mapping: dict) -> str:
        """Restore redacted values."""
        restored = text
        for placeholder, original in mapping.items():
            restored = restored.replace(placeholder, original)
        return restored

redactor = PIIRedactor()

def privacy_safe_chat(prompt: str, model: str):
    # Redact before sending
    redacted_prompt, mapping = redactor.redact(prompt)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": redacted_prompt}]
    )

    # Restore in response (if model referenced placeholders)
    content = response.choices[0].message.content
    restored_content = redactor.restore(content, mapping)

    return restored_content
```

### Custom PII Patterns
```python
# Add custom patterns for your domain
custom_patterns = {
    **PIIRedactor.PATTERNS,
    "employee_id": r'\bEMP-\d{6}\b',
    "account_number": r'\bACCT-\d{10}\b',
    "medical_record": r'\bMRN-\d{8}\b',
}

redactor = PIIRedactor(patterns=custom_patterns)
```

## Data Minimization

### Prompt Cleaning
```python
def clean_prompt(prompt: str) -> str:
    """Remove unnecessary data from prompts."""
    # Remove base64 encoded data
    prompt = re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/]+=*', '[DATA_REMOVED]', prompt)

    # Truncate very long strings that might be data
    lines = prompt.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line) > 1000:
            cleaned_lines.append(line[:1000] + '... [TRUNCATED]')
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)
```

### Minimal Context
```python
def create_minimal_prompt(
    question: str,
    context: str,
    max_context_chars: int = 10000
) -> str:
    """Create prompt with minimal necessary context."""
    # Truncate context if needed
    if len(context) > max_context_chars:
        context = context[:max_context_chars] + "\n[Context truncated]"

    return f"""Answer the following question using only the provided context.
Do not use any information beyond what is given.

Context:
{context}

Question: {question}

Answer:"""
```

## Audit Trail

### Request Logging
```python
import hashlib
from datetime import datetime
import json

class AuditLogger:
    """Log requests for compliance without storing content."""

    def __init__(self, log_file: str = "audit_log.jsonl"):
        self.log_file = log_file

    def log_request(
        self,
        user_id: str,
        model: str,
        prompt_hash: str,
        metadata: dict = None
    ):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "model": model,
            "prompt_hash": prompt_hash,  # Hash only, not content
            "metadata": metadata or {}
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    @staticmethod
    def hash_content(content: str) -> str:
        """Create hash of content for audit without storing content."""
        return hashlib.sha256(content.encode()).hexdigest()

audit = AuditLogger()

def audited_chat(prompt: str, model: str, user_id: str):
    # Log without storing content
    prompt_hash = audit.hash_content(prompt)
    audit.log_request(user_id, model, prompt_hash)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response
```

## Data Retention Controls

### Automatic Cleanup
```python
import os
from pathlib import Path
from datetime import datetime, timedelta

class DataRetention:
    """Manage data retention policies."""

    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days

    def cleanup_old_logs(self, log_dir: str):
        """Remove logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        log_path = Path(log_dir)

        removed = []
        for file in log_path.glob("*.log"):
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff:
                file.unlink()
                removed.append(file.name)

        return removed

    def cleanup_cache(self, cache_client):
        """Clear cached responses older than retention period."""
        # Implementation depends on cache backend
        pass

retention = DataRetention(retention_days=7)
```

### Request Anonymization
```python
import uuid

class AnonymizedClient:
    """Make requests without user-identifiable information."""

    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "",  # Remove referer
                "X-Title": "Anonymous",
            }
        )

    def chat(self, prompt: str, model: str):
        # Remove any identifying information from prompt
        cleaned_prompt = self._anonymize_prompt(prompt)

        return self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": cleaned_prompt}]
        )

    def _anonymize_prompt(self, prompt: str) -> str:
        # Redact PII
        prompt, _ = redactor.redact(prompt)
        return prompt
```

## Compliance Considerations

### GDPR Compliance
```python
class GDPRCompliance:
    """GDPR compliance helpers."""

    def __init__(self):
        self.consent_log = {}  # user_id -> consent_timestamp

    def record_consent(self, user_id: str):
        """Record user consent for AI processing."""
        self.consent_log[user_id] = datetime.utcnow().isoformat()

    def has_consent(self, user_id: str) -> bool:
        """Check if user has given consent."""
        return user_id in self.consent_log

    def process_with_consent(
        self,
        user_id: str,
        prompt: str,
        model: str
    ):
        if not self.has_consent(user_id):
            raise PermissionError(
                "User has not consented to AI processing"
            )

        return privacy_safe_chat(prompt, model)

    def right_to_erasure(self, user_id: str, data_stores: list):
        """Handle right to be forgotten requests."""
        for store in data_stores:
            store.delete_user_data(user_id)
        del self.consent_log[user_id]
        return {"status": "erased", "user_id": user_id}

gdpr = GDPRCompliance()
```

### Data Processing Agreement
```
When using OpenRouter for business:

1. Review OpenRouter's DPA (if available)
2. Review each model provider's DPA
3. Document data flows
4. Implement appropriate safeguards
5. Update privacy policies
```

## Security Best Practices

### Secure Configuration
```python
# Environment-based configuration
class SecureConfig:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        # Never log the full key
        self.masked_key = f"{self.api_key[:10]}...{self.api_key[-4:]}"

    def get_client(self):
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

# Never print or log full API key
config = SecureConfig()
print(f"Using key: {config.masked_key}")
```

### Request Validation
```python
def validate_request(prompt: str, max_length: int = 100000) -> bool:
    """Validate request before sending."""
    # Length check
    if len(prompt) > max_length:
        raise ValueError(f"Prompt exceeds {max_length} characters")

    # Check for potential injection
    dangerous_patterns = [
        r'ignore previous instructions',
        r'system:',
        r'<\|.*\|>',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValueError("Potentially dangerous content detected")

    return True
```
