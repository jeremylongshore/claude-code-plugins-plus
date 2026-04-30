---
name: procore-webhooks-events
description: "Procore webhooks events \u2014 construction management platform integration.\n\
  Use when working with Procore API for project management, RFIs, or submittals.\n\
  Trigger with phrases like \"procore webhooks events\", \"procore-webhooks-events\"\
  .\n"
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- procore
- construction
- project-management
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Procore Webhooks Events

## Overview
Implementation patterns for Procore webhooks events using the REST API with OAuth2 authentication.

## Prerequisites
- Completed `procore-install-auth` setup

## Instructions

### Step 1: API Call Pattern
```python
import os, requests

token_resp = requests.post("https://login.procore.com/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": os.environ["PROCORE_CLIENT_ID"],
    "client_secret": os.environ["PROCORE_CLIENT_SECRET"],
})
access_token = token_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

companies = requests.get("https://api.procore.com/rest/v1.0/companies", headers=headers)
print(f"Companies: {len(companies.json())}")
```

## Output
- Procore API integration for webhooks events

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Expired token | Re-authenticate |
| 429 Rate Limited | Too many requests | Implement backoff |
| 403 Forbidden | Insufficient permissions | Check project role |

## Resources
- [Procore Developers](https://developers.procore.com/)
- [REST API Reference](https://developers.procore.com/reference/rest)

## Next Steps
See related Procore skills for more workflows.
