---
name: klingai-common-errors
description: |
  Diagnose and fix common Kling AI API errors. Use when troubleshooting failed video generation
  or API issues. Trigger with phrases like 'kling ai error', 'klingai not working', 'fix klingai',
  'klingai failed'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, debugging, errors]

---
# Kling AI Common Errors

## Overview

Complete error reference for the Kling AI API. Covers HTTP status codes, task-level failures, JWT issues, and generation-specific problems with tested solutions.

## HTTP Error Codes

| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| `400` | Bad Request | Invalid parameters, malformed JSON | Validate all required fields; check `model_name` is valid |
| `401` | Unauthorized | Invalid/expired JWT token | Regenerate JWT; verify AK/SK; check `exp` claim |
| `402` | Payment Required | Insufficient credits | Top up API resource pack or subscription |
| `403` | Forbidden | Content policy violation or API disabled | Review prompt against content policy; enable API access |
| `404` | Not Found | Invalid task_id or wrong endpoint | Verify task_id; check endpoint path spelling |
| `429` | Too Many Requests | Rate limit exceeded | Implement exponential backoff (see pattern below) |
| `500` | Internal Server Error | Kling platform issue | Retry after 30s; if persistent, check status page |
| `502` | Bad Gateway | Upstream service unavailable | Retry with backoff; typically transient |
| `503` | Service Unavailable | System maintenance | Wait and retry; check announcements |

## Task-Level Failures

When HTTP returns `200` but `task_status` is `"failed"`:

| `task_status_msg` | Cause | Solution |
|-------------------|-------|----------|
| Content policy violation | Prompt contains restricted content | Remove violent, adult, or copyrighted references |
| Image quality too low | Source image is blurry or too small | Use image >= 300x300px, clear and sharp |
| Prompt too complex | Too many scene elements | Simplify to 1-2 subjects, clear action |
| Generation timeout | Internal processing exceeded limit | Retry; reduce duration from 10s to 5s |
| Invalid image format | Unsupported file type | Use JPG, PNG, or WebP |
| Mask dimension mismatch | Mask size differs from source | Ensure mask matches source image dimensions exactly |

## JWT Authentication Errors

### Problem: `401` on every request

```python
# WRONG — missing headers parameter
token = jwt.encode(payload, sk, algorithm="HS256")

# CORRECT — include explicit headers
token = jwt.encode(payload, sk, algorithm="HS256",
                   headers={"alg": "HS256", "typ": "JWT"})
```

### Problem: Token works then fails after 30 min

```python
# WRONG — token generated once at import time
TOKEN = generate_token()

# CORRECT — refresh before expiry
class TokenManager:
    def __init__(self, ak, sk):
        self.ak, self.sk = ak, sk
        self._token = None
        self._exp = 0

    @property
    def token(self):
        if time.time() >= self._exp - 300:  # 5 min buffer
            payload = {"iss": self.ak, "exp": int(time.time()) + 1800,
                       "nbf": int(time.time()) - 5}
            self._token = jwt.encode(payload, self.sk, algorithm="HS256",
                                     headers={"alg": "HS256", "typ": "JWT"})
            self._exp = int(time.time()) + 1800
        return self._token
```

## Rate Limit Handling

```python
import time
import requests

def request_with_backoff(method, url, headers, json=None, max_retries=5):
    """Retry with exponential backoff on 429 and 5xx errors."""
    for attempt in range(max_retries):
        response = method(url, headers=headers, json=json)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
            print(f"Rate limited. Retrying in {retry_after}s...")
            time.sleep(retry_after)
            continue
        elif response.status_code >= 500:
            wait = 2 ** attempt
            print(f"Server error {response.status_code}. Retrying in {wait}s...")
            time.sleep(wait)
            continue

        response.raise_for_status()
        return response

    raise RuntimeError(f"Max retries ({max_retries}) exceeded")
```

## Diagnostic Checklist

When a generation fails, check in order:

1. **Auth valid?** — Test with a simple GET request first
2. **Credits available?** — Check balance in developer console
3. **Model valid?** — Verify `model_name` matches catalog exactly
4. **Parameters valid?** — `duration` must be `"5"` or `"10"` (string, not int)
5. **Prompt clean?** — Remove special characters, keep under 2500 chars
6. **Image accessible?** — For I2V, verify image URL is publicly accessible
7. **Feature exclusivity?** — `image_tail`, `dynamic_masks`, and `camera_control` are mutually exclusive

## Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("kling")

def debug_request(method, url, headers, json=None):
    """Log request/response for debugging."""
    logger.debug(f"→ {method.__name__.upper()} {url}")
    logger.debug(f"→ Body: {json}")
    r = method(url, headers=headers, json=json)
    logger.debug(f"← Status: {r.status_code}")
    logger.debug(f"← Body: {r.text[:500]}")
    return r
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Content Policy](https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol)
- [Developer Portal](https://app.klingai.com/global/dev)
