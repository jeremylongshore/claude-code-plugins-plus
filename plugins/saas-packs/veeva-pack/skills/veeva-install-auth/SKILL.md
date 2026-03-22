---
name: veeva-install-auth
description: |
  Veeva Vault install auth with REST API and VQL.
  Use when integrating with Veeva Vault for life sciences document management.
  Trigger: "veeva install auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, life-sciences, crm, veeva]
compatible-with: claude-code
---

# Veeva Vault Install & Auth

## Overview

Authenticate with Veeva Vault REST API using session-based auth. Base URL: `https://{vault}.veevavault.com/api/{version}/`. All requests require a session ID obtained via username/password or OAuth 2.0.

## Instructions

### Step 1: Install VAPIL (Java) or HTTP Client

```bash
# Java (VAPIL - Vault API Library)
# Add to pom.xml or gradle
# https://github.com/veeva/vault-api-library

# Python/Node.js -- use HTTP client
pip install requests
# or
npm install axios
```

### Step 2: Obtain Session ID

```python
import requests

vault_url = "https://myvault.veevavault.com/api/v24.1"
auth_response = requests.post(f"{vault_url}/auth", data={
    "username": os.environ["VEEVA_USERNAME"],
    "password": os.environ["VEEVA_PASSWORD"],
})
session_id = auth_response.json()["sessionId"]
print(f"Session ID: {session_id[:20]}...")
```

### Step 3: Make Authenticated Request

```python
headers = {"Authorization": session_id}
response = requests.get(f"{vault_url}/metadata/objects", headers=headers)
print(f"Objects: {len(response.json()['objects'])}")
```

### Step 4: VQL Query

```python
query = "SELECT id, name__v, status__v FROM documents WHERE status__v = 'Approved'"
response = requests.post(f"{vault_url}/query", headers=headers, data={"q": query})
for doc in response.json().get("data", []):
    print(f"  {doc['name__v']} (ID: {doc['id']})")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_SESSION_ID` | Session expired | Re-authenticate |
| `INSUFFICIENT_ACCESS` | Missing permissions | Check security profile |
| `INVALID_DATA` | Bad VQL syntax | Validate query syntax |

## Resources

- [Vault API Reference](https://developer.veevavault.com/api/)
- [VQL Reference](https://developer.veevavault.com/vql/)
- [VAPIL Java SDK](https://developer.veevavault.com/sdk/)
- [Developer Portal](https://developer.veevavault.com/)

## Next Steps

Proceed to `veeva-hello-world` for document operations.
