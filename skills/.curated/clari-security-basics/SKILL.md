---
name: clari-security-basics
description: 'Secure Clari API tokens and implement data handling best practices.

  Use when managing API tokens, restricting data access,

  or implementing PII handling for exported forecast data.

  Trigger with phrases like "clari security", "clari api key rotation",

  "secure clari", "clari pii handling".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Security Basics

## Overview

Secure your Clari integration: API token management, exported data PII handling, and access control best practices.

## Prerequisites

- An approved secret manager and named API-token owner
- A documented data classification for forecast and rep-level exports
- Role-based access groups for production and non-production consumers
- A tested token-rotation and incident escalation path

## Instructions

### Step 1: Token Management

```bash
# Store token in secrets manager
aws secretsmanager create-secret \
  --name "clari/prod/api-token" \
  --secret-string "${CLARI_API_KEY}"

# In CI/CD, load from secrets
export CLARI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "clari/prod/api-token" --query SecretString --output text)
```

**Rotation**: Clari API tokens are generated per-user. To rotate, generate a new token in User Settings, update all consumers, then discard the old one.

### Step 2: Exported Data PII Handling

Clari export data contains PII (rep names, emails, deal amounts):

```python
def redact_pii(entries: list[dict]) -> list[dict]:
    """Redact PII from forecast entries for non-production use."""
    import hashlib

    redacted = []
    for entry in entries:
        r = entry.copy()
        if "ownerEmail" in r:
            r["ownerEmail"] = hashlib.sha256(
                r["ownerEmail"].encode()
            ).hexdigest()[:12] + "@redacted"
        if "ownerName" in r:
            r["ownerName"] = f"Rep-{hashlib.sha256(r['ownerName'].encode()).hexdigest()[:6]}"
        redacted.append(r)
    return redacted
```

### Step 3: Security Checklist

- [ ] API token in secrets manager, not in code
- [ ] `.env` files in `.gitignore`
- [ ] Exported data stored in access-controlled warehouse
- [ ] PII redacted in non-production environments
- [ ] Export download URLs are temporary -- do not cache
- [ ] Audit who has API token access
- [ ] Token regenerated if any team member leaves

## Error Handling

| Condition | Response |
|---|---|
| Token is exposed or a user departs | Revoke and replace it, audit access, and retain redacted incident evidence. |
| Export lands outside approved storage | Restrict access, remove the unauthorized copy through the approved retention process, and notify data governance. |
| PII is needed in a non-production test | Use synthetic or irreversibly redacted data; do not copy production records. |
| Access review finds excess privilege | Remove the role, confirm no dependent job fails, and document the decision. |

## Output

Create a security review record with token owner, secret reference, authorized
roles, data destinations, redaction status, rotation date, and exception
approvals. The record must never contain a live token, temporary download URL,
or unredacted forecast/rep data.

## Examples

When an analyst leaves, issue a replacement service token in the secret store,
update the affected job, prove that it runs with its assigned role, then revoke
the former user token. If an export was copied into a test workspace, quarantine
it and replace it with redacted data before work resumes.

## Resources

- [Clari Security](https://www.clari.com/trust)
- [Clari Developer Portal](https://developer.clari.com)

## Next Steps

For production deployment, see `clari-prod-checklist`.
