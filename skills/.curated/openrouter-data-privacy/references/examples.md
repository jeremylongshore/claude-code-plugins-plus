# Data Privacy Examples

## Python — PII Detection and Redaction

```python
import re
from dataclasses import dataclass

@dataclass
class PIIMatch:
    type: str
    value: str
    start: int
    end: int

class PIIDetector:
    """Detect and redact PII from text before sending to OpenRouter."""

    PATTERNS = {
        "email": r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
        "phone": r'\b(?:\+1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }

    PLACEHOLDERS = {
        "email": "[EMAIL_REDACTED]",
        "phone": "[PHONE_REDACTED]",
        "ssn": "[SSN_REDACTED]",
        "credit_card": "[CC_REDACTED]",
        "ip_address": "[IP_REDACTED]",
    }

    def detect(self, text: str) -> list[PIIMatch]:
        matches = []
        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text):
                matches.append(PIIMatch(
                    type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                ))
        return matches

    def redact(self, text: str) -> tuple[str, list[PIIMatch]]:
        """Redact PII and return cleaned text + list of findings."""
        findings = self.detect(text)
        redacted = text
        for pii_type, pattern in self.PATTERNS.items():
            redacted = re.sub(pattern, self.PLACEHOLDERS[pii_type], redacted)
        return redacted, findings

detector = PIIDetector()

# Example
text = "Contact John at john@example.com or 555-123-4567. SSN: 123-45-6789"
redacted, findings = detector.redact(text)

print(f"Original: {text}")
print(f"Redacted: {redacted}")
print(f"PII found: {len(findings)}")
for f in findings:
    print(f"  [{f.type}] '{f.value}'")
```

### Expected Output

```
Original: Contact John at john@example.com or 555-123-4567. SSN: 123-45-6789
Redacted: Contact John at [EMAIL_REDACTED] or [PHONE_REDACTED]. SSN: [SSN_REDACTED]
PII found: 3
  [email] 'john@example.com'
  [phone] '555-123-4567'
  [ssn] '123-45-6789'
```

## Python — Privacy-Safe API Wrapper

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def privacy_safe_completion(prompt: str, model: str = "openai/gpt-3.5-turbo",
                            block_on_pii: bool = False) -> str:
    """Make an API call with PII protection."""
    redacted, findings = detector.redact(prompt)

    if findings and block_on_pii:
        raise ValueError(
            f"PII detected in prompt: {[f.type for f in findings]}. "
            "Remove sensitive data before sending."
        )

    if findings:
        print(f"[Privacy] Redacted {len(findings)} PII instances before sending")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": redacted}],
        max_tokens=300,
    )
    return response.choices[0].message.content

# Usage — auto-redacts PII
result = privacy_safe_completion(
    "Analyze this customer: email john@test.com, phone 555-0100"
)
# [Privacy] Redacted 2 PII instances before sending
print(result)

# Usage — block on PII (strict mode)
try:
    privacy_safe_completion("SSN is 123-45-6789", block_on_pii=True)
except ValueError as e:
    print(f"Blocked: {e}")
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
