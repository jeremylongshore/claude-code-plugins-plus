---
name: ramp-security-basics
description: |
  Ramp security basics — corporate card and expense management API integration.
  Use when working with Ramp for card management, expenses, or accounting sync.
  Trigger with phrases like "ramp security basics", "ramp-security-basics", "corporate card API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ramp, fintech, expenses, corporate-cards]
compatible-with: claude-code, codex, openclaw
---

# Ramp Security Basics

## Overview
Implementation patterns for Ramp security basics using the Developer API with OAuth2 authentication.

## Prerequisites
- Completed `ramp-install-auth` setup

## Instructions

### Step 1: API Call Pattern
```python
import os, requests

# Obtain token
token_resp = requests.post(f"{os.environ['RAMP_BASE_URL'].replace('/v1','')}/v1/token", data={
    "grant_type": "client_credentials",
    "client_id": os.environ["RAMP_CLIENT_ID"],
    "client_secret": os.environ["RAMP_CLIENT_SECRET"],
})
access_token = token_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

cards = requests.get(f"{os.environ['RAMP_BASE_URL']}/cards", headers=headers)
print(f"Cards: {len(cards.json()['data'])}")
```

## Output
- Ramp API integration for security basics

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Expired token | Re-authenticate |
| 429 Rate Limited | Too many requests | Implement backoff |
| 403 Forbidden | Insufficient permissions | Check API app permissions |

## Resources
- [Ramp API Documentation](https://docs.ramp.com/)
- [Authorization](https://docs.ramp.com/developer-api/v1/authorization)

## Next Steps
See related Ramp skills for more workflows.
