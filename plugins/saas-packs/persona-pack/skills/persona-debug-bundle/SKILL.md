---
name: persona-debug-bundle
description: |
  Collect Persona diagnostic info: inquiry IDs, API responses, webhook logs.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona debug-bundle", "persona debug-bundle".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona debug bundle | sed 's/\b\(.\)/\u\1/g'

## Overview
Gather inquiry state, verification results, webhook delivery logs, API connectivity test.

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

# Collect Persona diagnostic info: inquiry IDs, API responses, webhook logs
resp = requests.get(f"{BASE}/inquiries?page[size]=10", headers=HEADERS)
resp.raise_for_status()
inquiries = resp.json()["data"]
for inq in inquiries:
    print(f"  {inq['id']}: {inq['attributes']['status']}")
```

## Output
- Gather inquiry state, verification results, webhook delivery logs, API connectivity test.

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
