---
name: remofirst-install-auth
description: |
  RemoFirst install auth — global HR, EOR, and payroll platform integration.
  Use when working with RemoFirst for global employment, payroll, or compliance.
  Trigger with phrases like "remofirst install auth", "remofirst-install-auth", "global HR API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, remofirst, hr, eor, payroll, global-employment]
compatible-with: claude-code, codex, openclaw
---

# RemoFirst Install Auth

## Overview
Set up RemoFirst API authentication for global HR and payroll integration. RemoFirst provides API access for enterprise customers.

## Prerequisites
- RemoFirst enterprise account
- API credentials from RemoFirst support team
- Node.js 18+ or Python 3.9+

## Instructions

### Step 1: Get API Credentials
```text
1. Contact RemoFirst support for API access
2. Receive API key and base URL
3. Note: Sandbox environment available for testing
```

### Step 2: Configure Environment
```bash
# .env
REMOFIRST_API_KEY=your_api_key
REMOFIRST_BASE_URL=https://api.remofirst.com/v1
```

### Step 3: Initialize Client
```python
import os, requests

class RemoFirstClient:
    def __init__(self):
        self.base_url = os.environ["REMOFIRST_BASE_URL"]
        self.headers = {
            "Authorization": f"Bearer {os.environ['REMOFIRST_API_KEY']}",
            "Content-Type": "application/json",
        }

    def get(self, path, params=None):
        resp = requests.get(f"{self.base_url}{path}", headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, data):
        resp = requests.post(f"{self.base_url}{path}", headers=self.headers, json=data)
        resp.raise_for_status()
        return resp.json()

client = RemoFirstClient()
```

### Step 4: Verify Connection
```python
company = client.get("/company")
print(f"Connected! Company: {company['name']}")
print(f"Countries: {len(company.get('active_countries', []))}")
```

## Output
- API credentials configured
- Client initialized with authentication
- Connection verified

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Contact RemoFirst support |
| `403 Forbidden` | API access not enabled | Request API access from account manager |
| Connection refused | Wrong base URL | Verify URL with RemoFirst |

## Resources
- [RemoFirst](https://www.remofirst.com)
- [Global HR Solutions](https://www.remofirst.com/solutions/human-resources)

## Next Steps
First API call: `remofirst-hello-world`
