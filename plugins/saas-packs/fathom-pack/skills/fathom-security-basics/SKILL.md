---
name: fathom-security-basics
description: |
  Secure Fathom API keys and handle meeting data privacy.
  Trigger with phrases like "fathom security", "fathom api key safety", "fathom privacy".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Security Basics

## API Key Management

- API keys are per-user and access meetings you recorded OR shared to your team
- Store in secrets manager, never in code
- Regenerate if compromised

## Meeting Data Privacy

- Transcripts contain PII (names, spoken content)
- Action items may reference confidential business decisions
- Always redact before logging or analytics

```python
def redact_transcript(segments: list[dict]) -> list[dict]:
    import re
    email_pattern = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    return [{
        **seg,
        "text": email_pattern.sub("[REDACTED_EMAIL]", seg["text"])
    } for seg in segments]
```

## Security Checklist

- [ ] API key in secrets manager
- [ ] Meeting data encrypted at rest
- [ ] PII redacted in non-production environments
- [ ] Webhook endpoints use HTTPS
- [ ] Access logs track API key usage

## Next Steps

For production readiness, see `fathom-prod-checklist`.
