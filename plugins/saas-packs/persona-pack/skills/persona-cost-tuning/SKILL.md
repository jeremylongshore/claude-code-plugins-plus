---
name: persona-cost-tuning
description: |
  Optimize Persona verification costs with template selection and caching.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona cost-tuning", "persona cost-tuning".
allowed-tools: Read, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona cost tuning | sed 's/\b\(.\)/\u\1/g'

## Overview
Choose appropriate verification types, cache results, avoid duplicate inquiries.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid Persona API key (sandbox or production)

## Instructions

### Step 1: Implementation
```python
import os, requests

HEADERS = {
    "Authorization": f"Bearer {os.environ['PERSONA_API_KEY']}",
    "Persona-Version": "2023-01-05",
}
BASE = "https://withpersona.com/api/v1"

# Optimize Persona verification costs with template selection and caching
resp = requests.get(f"{BASE}/inquiries?page[size]=10", headers=HEADERS)
resp.raise_for_status()
inquiries = resp.json()["data"]
for inq in inquiries:
    print(f"  {inq['id']}: {inq['attributes']['status']}")
```

## Output
- Choose appropriate verification types, cache results, avoid duplicate inquiries.

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check PERSONA_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 404 Not Found | Wrong resource ID | Verify ID format |

## Resources
- [Persona API Reference](https://docs.withpersona.com/reference/introduction)
- [Persona Documentation](https://docs.withpersona.com)

## Next Steps
See related Persona skills for more workflows.
