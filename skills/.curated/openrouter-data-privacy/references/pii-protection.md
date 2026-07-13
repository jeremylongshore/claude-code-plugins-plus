# Pii Protection

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
