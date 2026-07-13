---
name: openrouter-data-privacy
description: 'Implement data privacy controls for OpenRouter API usage. Use when handling
  PII, meeting GDPR/CCPA requirements, or protecting sensitive data in prompts. Triggers:
  ''openrouter privacy'', ''openrouter pii'', ''openrouter gdpr'', ''openrouter data
  handling''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- privacy
- security
- compliance
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Data Privacy

## Overview

When sending data through OpenRouter to upstream LLM providers, you're responsible for ensuring prompts don't leak PII inappropriately. OpenRouter itself does not train on API data, but each upstream provider has its own data retention and training policies. This skill covers PII detection and redaction, placeholder substitution, provider selection for privacy, and consent tracking.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK (`pip install openai`) — every pattern in this skill is Python
- A sensitivity classification for your workloads (`public` / `standard` / `sensitive`) so `privacy_aware_completion()` can route each one
- A list of providers your org approves for sensitive data, to plug into `provider.order` with `allow_fallbacks: False`

## Instructions

1. Start with PII Detection and Redaction: adapt `PII_RULES` (email, phone, SSN, credit card, `sk-or-v1-` API keys, IPs) to your data, then run `scan_and_redact()` on representative inputs and review the `findings` for false positives.
2. When downstream code needs the original values back, use the Placeholder Substitution Pattern instead of plain redaction — `PrivacyProxy.anonymize()` before the API call, `deanonymize()` on the model's reply.
3. Classify each workload and route it via Provider Selection for Privacy: `privacy_aware_completion()` maps sensitivity to a model plus a `provider` block (`order: ["Anthropic"]`, `allow_fallbacks: False` for standard/sensitive).
4. Wire the Privacy Middleware into every call path, choosing `block_on_pii=True` (raise on detection) or `auto_redact=True` (scrub and continue) per workload.
5. Apply the Enterprise Considerations: hash logged prompts (SHA-256) for GDPR right-to-erasure, and use BYOK for the most sensitive workloads.

## PII Detection and Redaction

```python
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class PiiScanResult:
    clean_text: str
    findings: list[dict]
    has_pii: bool

PII_RULES = [
    ("email", r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    ("phone", r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    ("ssn", r'\b\d{3}-\d{2}-\d{4}\b'),
    ("credit_card", r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
    ("api_key", r'\bsk-or-v1-[a-zA-Z0-9]+\b'),
    ("ip_address", r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
]

REPLACEMENTS = {
    "email": "[EMAIL]", "phone": "[PHONE]", "ssn": "[SSN]",
    "credit_card": "[CARD]", "api_key": "[API_KEY]", "ip_address": "[IP]",
}

def scan_and_redact(text: str) -> PiiScanResult:
    """Scan text for PII and return redacted version with findings."""
    findings = []
    clean = text
    for pii_type, pattern in PII_RULES:
        matches = re.findall(pattern, clean)
        for match in matches:
            findings.append({"type": pii_type, "value_prefix": match[:4] + "..."})
        clean = re.sub(pattern, REPLACEMENTS[pii_type], clean)

    return PiiScanResult(clean_text=clean, findings=findings, has_pii=len(findings) > 0)
```

## Placeholder Substitution Pattern

```python
import os, uuid
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

class PrivacyProxy:
    """Replace PII with placeholders before API, restore after."""

    def __init__(self):
        self._map: dict[str, str] = {}

    def anonymize(self, text: str) -> str:
        """Replace PII with unique placeholders."""
        result = scan_and_redact(text)
        if not result.has_pii:
            return text

        # Use deterministic placeholders for consistent replacement
        anonymized = text
        for pii_type, pattern in PII_RULES:
            for match in re.finditer(pattern, anonymized):
                original = match.group()
                if original not in self._map:
                    placeholder = f"[{pii_type.upper()}_{len(self._map)}]"
                    self._map[placeholder] = original
                else:
                    placeholder = next(k for k, v in self._map.items() if v == original)
                anonymized = anonymized.replace(original, placeholder, 1)
        return anonymized

    def deanonymize(self, text: str) -> str:
        """Restore original values from placeholders."""
        result = text
        for placeholder, original in self._map.items():
            result = result.replace(placeholder, original)
        return result

# Usage
proxy = PrivacyProxy()
user_input = "Contact john@example.com or call 555-123-4567"
safe_input = proxy.anonymize(user_input)
# safe_input = "Contact [EMAIL_0] or call [PHONE_1]"

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": safe_input}],
    max_tokens=200,
)
# Restore PII in the response if model referenced it
result = proxy.deanonymize(response.choices[0].message.content)
```

## Provider Selection for Privacy

```python
# Force specific provider to control data handling
def privacy_aware_completion(messages, sensitivity="standard"):
    """Route to appropriate provider based on data sensitivity."""

    PRIVACY_CONFIG = {
        "public": {
            "model": "openai/gpt-4o-mini",
            "provider": None,  # Any provider OK
        },
        "standard": {
            "model": "anthropic/claude-3.5-sonnet",
            "provider": {"order": ["Anthropic"], "allow_fallbacks": False},
        },
        "sensitive": {
            "model": "anthropic/claude-3.5-sonnet",
            "provider": {"order": ["Anthropic"], "allow_fallbacks": False},
            # Add PII redaction as mandatory pre-processing
        },
    }

    config = PRIVACY_CONFIG.get(sensitivity, PRIVACY_CONFIG["standard"])
    extra = {}
    if config["provider"]:
        extra["extra_body"] = {"provider": config["provider"]}

    return client.chat.completions.create(
        model=config["model"],
        messages=messages,
        max_tokens=1024,
        **extra,
    )
```

## Privacy Middleware

```python
class PrivacyMiddleware:
    """Enforce privacy policies before every API call."""

    def __init__(self, block_on_pii: bool = False, auto_redact: bool = True):
        self.block_on_pii = block_on_pii
        self.auto_redact = auto_redact

    def process(self, messages: list[dict]) -> list[dict]:
        """Scan and optionally redact PII from all messages."""
        processed = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                result = scan_and_redact(content)
                if result.has_pii:
                    if self.block_on_pii:
                        raise ValueError(f"PII detected: {[f['type'] for f in result.findings]}")
                    if self.auto_redact:
                        msg = {**msg, "content": result.clean_text}
            processed.append(msg)
        return processed
```

## Output

The privacy flows in this skill produce:

- A `PiiScanResult` per scan: `clean_text` with placeholders substituted, `findings` (PII type + first-4-chars value prefix per match), and a `has_pii` flag
- Anonymized prompts like `"Contact [EMAIL_0] or call [PHONE_1]"` plus the placeholder→original map that `deanonymize()` uses to restore values in the response
- Chat completions served only by approved providers when the `provider.order` + `allow_fallbacks: False` config is applied
- A `ValueError` listing the detected PII types when `PrivacyMiddleware` runs with `block_on_pii=True`

## Examples

Scanning a support message before it leaves your infrastructure:

```python
result = scan_and_redact("Contact john@example.com or call 555-123-4567")
print(result.clean_text)  # Contact [EMAIL] or call [PHONE]
print(result.has_pii)     # True
print(result.findings)    # [{'type': 'email', 'value_prefix': 'john...'}, {'type': 'phone', ...}]
```

To keep the values recoverable, run the same input through `PrivacyProxy.anonymize()` instead, send the placeholder version to the model, then `deanonymize()` the reply. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| PII detected in prompt | User input contains sensitive data | Auto-redact or block and prompt user to remove |
| Provider retained data | Using provider with training-on-API-data | Switch to Anthropic or use BYOK |
| Placeholder in response | Model used placeholder literally | Map it back with `deanonymize()` |
| False positive PII match | Regex too aggressive | Tune patterns; use NLP-based PII detection for accuracy |

## Enterprise Considerations

- OpenRouter does not train on API data; check each upstream provider's data use policy separately
- Use `provider.order` + `allow_fallbacks: false` to ensure data only flows to approved providers
- Implement PII redaction as middleware that runs on every request, not optional per-call
- For GDPR right-to-erasure: don't log raw prompts -- hash them (SHA-256)
- Use BYOK for sensitive workloads so data flows directly to the provider under your account
- Build a data classification system that auto-routes based on sensitivity level

## References

- Examples | Errors
- [Privacy Policy](https://openrouter.ai/privacy) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
