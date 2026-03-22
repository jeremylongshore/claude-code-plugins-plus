---
name: klingai-install-auth
description: |
  Set up Kling AI API authentication with JWT tokens. Use when starting a new Kling AI
  integration or troubleshooting auth issues. Trigger with phrases like 'kling ai setup',
  'klingai api key', 'kling ai authentication', 'configure klingai'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, api, authentication]

---
# Kling AI Install & Auth

## Overview

Kling AI uses JWT (JSON Web Token) authentication. You generate a token from your Access Key (AK) and Secret Key (SK), then pass it as a Bearer token in every request. Tokens expire after 30 minutes.

**Base URL:** `https://api.klingai.com/v1`

## Prerequisites

- Kling AI account at [klingai.com](https://klingai.com)
- API access enabled (self-service, no waitlist)
- Python 3.8+ with `PyJWT` or Node.js 18+

## Step 1 — Get Credentials

1. Sign in at [app.klingai.com/global/dev](https://app.klingai.com/global/dev)
2. Navigate to **API Keys** in the developer console
3. Click **Create API Key** to generate an Access Key + Secret Key pair
4. Store both values securely — the Secret Key is shown only once

```bash
# .env file
KLING_ACCESS_KEY="ak_your_access_key_here"
KLING_SECRET_KEY="sk_your_secret_key_here"
```

## Step 2 — Generate JWT Token

### Python

```python
import jwt
import time
import os

def generate_kling_token():
    """Generate a JWT token for Kling AI API authentication."""
    ak = os.environ["KLING_ACCESS_KEY"]
    sk = os.environ["KLING_SECRET_KEY"]

    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,  # 30 min expiry
        "nbf": int(time.time()) - 5,     # valid 5s ago (clock skew)
    }

    return jwt.encode(payload, sk, algorithm="HS256", headers=headers)

token = generate_kling_token()
# Use: Authorization: Bearer <token>
```

### Node.js

```javascript
import jwt from "jsonwebtoken";

function generateKlingToken() {
  const ak = process.env.KLING_ACCESS_KEY;
  const sk = process.env.KLING_SECRET_KEY;

  const payload = {
    iss: ak,
    exp: Math.floor(Date.now() / 1000) + 1800,
    nbf: Math.floor(Date.now() / 1000) - 5,
  };

  return jwt.sign(payload, sk, { algorithm: "HS256", header: { typ: "JWT" } });
}
```

## Step 3 — Verify Authentication

```python
import requests

BASE_URL = "https://api.klingai.com/v1"
token = generate_kling_token()

response = requests.get(
    f"{BASE_URL}/videos/text2video",  # any endpoint to test auth
    headers={"Authorization": f"Bearer {token}"},
)

if response.status_code == 401:
    print("Auth failed — check AK/SK values")
elif response.status_code in (200, 400):
    print("Auth working — credentials valid")
```

## Token Management Pattern

```python
import time

class KlingAuth:
    """Auto-refreshing JWT token manager."""

    def __init__(self, access_key: str, secret_key: str, buffer_sec: int = 300):
        self.ak = access_key
        self.sk = secret_key
        self.buffer = buffer_sec  # refresh 5 min before expiry
        self._token = None
        self._expires_at = 0

    @property
    def token(self) -> str:
        if time.time() >= (self._expires_at - self.buffer):
            self._refresh()
        return self._token

    def _refresh(self):
        now = int(time.time())
        payload = {"iss": self.ak, "exp": now + 1800, "nbf": now - 5}
        self._token = jwt.encode(payload, self.sk, algorithm="HS256",
                                  headers={"alg": "HS256", "typ": "JWT"})
        self._expires_at = now + 1800

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid/expired JWT | Regenerate token, check AK/SK |
| `403 Forbidden` | API access not enabled | Enable API in developer console |
| JWT decode error | Wrong secret key | Verify SK matches the AK pair |
| Token expired | >30 min since generation | Implement auto-refresh (see above) |
| Clock skew error | Server time mismatch | Use `nbf: now - 5` for tolerance |

## Security Checklist

- Never commit AK/SK to version control
- Use `.env` files with `.gitignore` exclusion
- Rotate keys quarterly via the developer console
- Use separate keys per environment (dev/staging/prod)
- Set `exp` to 1800s max (Kling enforces this ceiling)

## Resources

- [Kling AI Developer Portal](https://app.klingai.com/global/dev)
- [API Key Management](https://app.klingai.com/global/dev/api-key)
- [Quick Start Guide](https://app.klingai.com/global/dev/document-api/quickStart/userManual)
