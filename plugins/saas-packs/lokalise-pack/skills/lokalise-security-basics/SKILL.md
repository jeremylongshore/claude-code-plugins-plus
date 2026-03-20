---
name: lokalise-security-basics
description: |
  Apply Lokalise security best practices for API tokens and access control.
  Use when securing API tokens, implementing least privilege access,
  or auditing Lokalise security configuration.
  Trigger with phrases like "lokalise security", "lokalise secrets",
  "secure lokalise", "lokalise API token security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Security Basics

## Overview
Security practices for Lokalise translation management integrations. Lokalise handles translation strings that may contain user-facing content, brand messaging, and occasionally PII embedded in translation keys.

## Prerequisites
- Lokalise API token provisioned
- Understanding of token permission scopes
- Secret management infrastructure

## Instructions

### Step 1: Token Scope Management

Lokalise tokens can have different permission levels. Use the minimum scope needed.

```python
import os

# BAD: using admin token for read-only operations
# GOOD: create scoped tokens per use case

LOKALISE_READ_TOKEN = os.environ.get("LOKALISE_READ_TOKEN")    # read-only
LOKALISE_WRITE_TOKEN = os.environ.get("LOKALISE_WRITE_TOKEN")  # read + write
LOKALISE_ADMIN_TOKEN = os.environ.get("LOKALISE_ADMIN_TOKEN")  # admin (CI only)

def get_client(scope: str = "read"):
    import lokalise
    tokens = {"read": LOKALISE_READ_TOKEN, "write": LOKALISE_WRITE_TOKEN, "admin": LOKALISE_ADMIN_TOKEN}
    token = tokens.get(scope)
    if not token:
        raise RuntimeError(f"LOKALISE_{scope.upper()}_TOKEN not configured")
    return lokalise.Client(token)
```

### Step 2: Protect Translation Content

Translation strings may contain interpolation variables. Validate before processing.

```python
import re

def validate_translation(key: str, value: str) -> list[str]:
    issues = []
    # Check for potential code injection in translations
    if re.search(r'<script|javascript:|on\w+=', value, re.IGNORECASE):
        issues.append(f"Potential XSS in translation {key}")
    # Check for leaked credentials
    if re.search(r'(api_key|password|secret|token)\s*[:=]', value, re.IGNORECASE):
        issues.append(f"Possible credential in translation {key}")
    # Validate interpolation variables match expected format
    placeholders = re.findall(r'\{[^}]+\}|%[sd]|\$\{[^}]+\}', value)
    for p in placeholders:
        if re.search(r'[<>\'"]', p):
            issues.append(f"Suspicious placeholder in {key}: {p}")
    return issues
```

### Step 3: CI/CD Token Security

```yaml
# GitHub Actions: use repository secrets
name: Sync Translations
on: push
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Pull translations
        env:
          LOKALISE_TOKEN: ${{ secrets.LOKALISE_READ_TOKEN }}
        run: |
          lokalise2 file download \
            --token $LOKALISE_TOKEN \
            --project-id ${{ vars.LOKALISE_PROJECT_ID }} \
            --format json \
            --dest ./locales/
```

### Step 4: Audit Translation Changes

Track who changed what translations for compliance.

```python
def audit_translation_change(project_id: str, key: str, old_value: str, new_value: str, user: str):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "key": key,
        "user": user,
        "action": "update",
        "changes": {"old_length": len(old_value), "new_length": len(new_value)}
        # Don't log actual content if it may contain PII
    }
    audit_logger.info("Translation changed", extra=log_entry)
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Token leaked in CI logs | Token in command output | Use environment variables, mask in CI |
| XSS via translations | Unsanitized translation content | Validate translations before use |
| Overprivileged access | Using admin token everywhere | Create scoped read/write tokens |
| Unauthorized changes | No audit trail | Log translation changes with user info |

## Examples

### Security Check Script
```bash
# Scan for hardcoded tokens
grep -rn "LOKALISE" --include="*.py" --include="*.ts" src/ | grep -v "os.environ\|process.env"
```

## Resources
- [Lokalise API Auth](https://developers.lokalise.com/reference/api-authentication)
- [Lokalise Security](https://lokalise.com/security)

## Output

- Scoped token configuration: separate `LOKALISE_READ_TOKEN`, `LOKALISE_WRITE_TOKEN`, and `LOKALISE_ADMIN_TOKEN` environment variables with least-privilege assignment
- Translation content validator catching XSS payloads, leaked credentials, and suspicious interpolation placeholders
- CI/CD workflow using repository secrets with masked token output and read-only scope for pull operations
- Audit logging function recording translation changes with timestamp, user, project, and key metadata (content omitted for PII safety)
- Hardcoded token scan command for pre-commit or CI gate verification