---
name: openrouter-install-auth
description: |
  Set up OpenRouter API authentication and configure API keys. Use when starting a new OpenRouter integration, rotating keys, or troubleshooting auth issues. Triggers: 'openrouter setup', 'openrouter api key', 'configure openrouter auth', 'sk-or key'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, api, authentication, setup]

---
# OpenRouter Install & Auth

## Overview

Set up OpenRouter API credentials, configure the OpenAI-compatible client, verify authentication, and check credit balance. OpenRouter keys start with `sk-or-v1-` and authenticate against `https://openrouter.ai/api/v1`.

## Prerequisites

- OpenRouter account (free at [openrouter.ai](https://openrouter.ai))
- Python 3.8+ or Node.js 18+
- OpenAI SDK (`pip install openai` or `npm install openai`)

## Quick Setup

### 1. Generate an API Key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Click **Create Key**, name it (e.g., `my-app-dev`)
3. Copy the `sk-or-v1-...` value immediately (shown only once)
4. Optionally set a credit limit on the key for spend control

### 2. Configure Environment

```bash
# .env file (add .env to .gitignore!)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Or export directly
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

### 3. Initialize the Client

**Python:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://your-app.com",  # For analytics attribution
        "X-Title": "Your App Name",               # Shows in dashboard
    },
)
```

**TypeScript:**
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://your-app.com",
    "X-Title": "Your App Name",
  },
});
```

### 4. Verify Authentication

```python
# Quick auth + credit check
import requests

resp = requests.get(
    "https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
)
data = resp.json()["data"]
print(f"Key: {data['label']}")
print(f"Credits used: ${data['usage']:.4f}")
print(f"Credit limit: ${data.get('limit', 'unlimited')}")
print(f"Free tier: {data['is_free_tier']}")
print(f"Rate limit: {data['rate_limit']['requests']} req / {data['rate_limit']['interval']}")
```

### 5. Send a Test Request

```python
response = client.chat.completions.create(
    model="google/gemma-2-9b-it:free",  # Free model for testing
    messages=[{"role": "user", "content": "Say hello"}],
    max_tokens=50,
)
print(response.choices[0].message.content)
print(f"Tokens: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out")
```

## Required Headers

| Header | Purpose | Required |
|--------|---------|----------|
| `Authorization` | `Bearer sk-or-v1-...` | Yes |
| `HTTP-Referer` | Your app URL for dashboard attribution | Recommended |
| `X-Title` | App name shown in OpenRouter dashboard | Recommended |
| `Content-Type` | `application/json` | Yes (POST) |

## Key Formats

| Type | Pattern | Purpose |
|------|---------|---------|
| Standard key | `sk-or-v1-...` | API access (chat completions, models) |
| Management key | `sk-or-v1-...` | Key provisioning only (cannot call completions) |
| BYOK provider key | Varies by provider | Bring-your-own-key for direct provider access |

## Error Handling

| HTTP | Error Code | Cause | Fix |
|------|-----------|-------|-----|
| 401 | `invalid_api_key` | Key malformed, revoked, or wrong | Regenerate at [openrouter.ai/keys](https://openrouter.ai/keys) |
| 401 | `missing_api_key` | No `Authorization` header | Add `Authorization: Bearer sk-or-v1-...` |
| 403 | `insufficient_credits` | Zero balance on paid model | Add credits at [openrouter.ai/credits](https://openrouter.ai/credits) or use `:free` model |
| 403 | `key_disabled` | Key was disabled by admin | Re-enable in dashboard or create new key |

## Key Rotation

```python
# Programmatic key management via Management API
import requests

MGMT_KEY = os.environ["OPENROUTER_MGMT_KEY"]  # Management key, not API key

# Create a new key
resp = requests.post(
    "https://openrouter.ai/api/v1/keys",
    headers={"Authorization": f"Bearer {MGMT_KEY}"},
    json={"name": "my-app-prod-v2", "limit": 100.0},
)
new_key = resp.json()["data"]["key"]  # sk-or-v1-...

# List existing keys
keys = requests.get(
    "https://openrouter.ai/api/v1/keys",
    headers={"Authorization": f"Bearer {MGMT_KEY}"},
).json()
```

## Enterprise Considerations

- Store keys in a secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault)
- Use management keys to provision per-service API keys programmatically
- Set credit limits per key to isolate blast radius
- Rotate keys on a schedule (90 days recommended)
- Add secret scanning to CI pipelines (e.g., `gitleaks`, `trufflehog`)
- Use BYOK for direct provider billing when volume justifies it

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) | [Auth Docs](https://openrouter.ai/docs/api/reference/authentication) | [Key Provisioning](https://openrouter.ai/docs/guides/overview/auth/provisioning-api-keys)
