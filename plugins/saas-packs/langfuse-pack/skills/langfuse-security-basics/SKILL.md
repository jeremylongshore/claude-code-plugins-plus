---
name: langfuse-security-basics
description: |
  Implement Langfuse security best practices for API keys and data privacy.
  Use when securing Langfuse integration, protecting API keys,
  or implementing data privacy controls for LLM observability.
  Trigger with phrases like "langfuse security", "langfuse API key security",
  "langfuse data privacy", "secure langfuse", "langfuse PII".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse Security Basics

## Overview
Security practices for Langfuse LLM observability integrations. Langfuse captures prompts, completions, and metadata from LLM calls -- making data privacy and access control critical since traced data may contain PII.

## Prerequisites
- Langfuse instance (cloud or self-hosted)
- API keys provisioned
- Understanding of data privacy requirements

## Instructions

### Step 1: Credential Separation

Langfuse uses separate public and secret keys. Only the secret key should be protected.

```python
import os

# Public key: safe for client-side (identifies project)
LANGFUSE_PUBLIC_KEY = os.environ["LANGFUSE_PUBLIC_KEY"]

# Secret key: NEVER expose (grants write access to traces)
LANGFUSE_SECRET_KEY = os.environ["LANGFUSE_SECRET_KEY"]

# Host (for self-hosted)
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Validate on startup
assert LANGFUSE_SECRET_KEY, "LANGFUSE_SECRET_KEY required"
assert not LANGFUSE_SECRET_KEY.startswith("pk-"), "Using public key as secret key!"
```

### Step 2: PII Scrubbing Before Tracing

Langfuse stores everything you send. Scrub PII before tracing.

```python
import re
from langfuse import Langfuse

langfuse = Langfuse()

def scrub_pii(text: str) -> str:
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b', '[EMAIL]', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    return text

def traced_llm_call(prompt: str, user_id: str):
    trace = langfuse.trace(
        name="llm-call",
        user_id=user_id,  # OK: user IDs are fine
        input=scrub_pii(prompt),  # scrub before tracing
    )
    response = call_llm(prompt)  # send original to LLM
    trace.update(output=scrub_pii(response))  # scrub output too
    return response
```

### Step 3: Access Control for Self-Hosted

```yaml
# docker-compose.yml for self-hosted Langfuse
services:
  langfuse:
    image: langfuse/langfuse:latest
    environment:
      - AUTH_DISABLE_SIGNUP=true           # prevent open registration
      - AUTH_DOMAINS_WITH_SSO_ENFORCEMENT=company.com  # require SSO
      - LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER  # least privilege default
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}   # encrypt data at rest
```

### Step 4: Trace Data Retention

Configure automatic cleanup of old traces to limit exposure.

```python
# Self-hosted: set retention via environment
# LANGFUSE_RETENTION_DAYS=90

# Cloud: use API to delete old traces
from datetime import datetime, timedelta

def cleanup_old_traces(langfuse: Langfuse, max_age_days: int = 90):
    cutoff = datetime.now() - timedelta(days=max_age_days)
    # Use Langfuse API to list and delete traces older than cutoff
    # Implement based on your Langfuse version's API
    print(f"Cleaning traces older than {cutoff.isoformat()}")
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in traces | Not scrubbing before trace | Apply PII scrubbing to inputs/outputs |
| Secret key leaked | Wrong key in client code | Validate key prefix (sk- vs pk-) |
| Unauthorized access | No SSO enforcement | Enable `AUTH_DOMAINS_WITH_SSO_ENFORCEMENT` |
| Data accumulation | No retention policy | Set `LANGFUSE_RETENTION_DAYS` |

## Examples

### Secure Initialization
```python
from langfuse import Langfuse
langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
```

## Resources
- [Langfuse Security Docs](https://langfuse.com/docs/data-security-privacy)
- [Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)
