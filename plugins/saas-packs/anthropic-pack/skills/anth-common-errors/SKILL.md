---
name: anth-common-errors
description: |
  Diagnose and fix Anthropic Claude API errors by HTTP status code.
  Use when encountering API errors, debugging failed requests,
  or troubleshooting authentication, rate limiting, or input validation issues.
  Trigger with phrases like "anthropic error", "claude api error",
  "fix anthropic 429", "claude not working", "debug claude api".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Common Errors

## Overview

Quick reference for all Claude API error types with exact HTTP codes, error bodies, and fixes. The API returns errors as JSON: `{"type": "error", "error": {"type": "...", "message": "..."}}`.

## Error Reference

### 400 — `invalid_request_error`

```json
{"type": "error", "error": {"type": "invalid_request_error", "message": "messages: roles must alternate between \"user\" and \"assistant\""}}
```

**Common causes and fixes:**

| Message Pattern | Cause | Fix |
|----------------|-------|-----|
| `messages: roles must alternate` | Consecutive same-role messages | Merge adjacent user/assistant messages |
| `max_tokens: must be >= 1` | Missing or zero `max_tokens` | Always set `max_tokens` (required param) |
| `model: invalid model id` | Typo in model name | Use exact ID: `claude-sonnet-4-20250514` |
| `messages.0.content: empty` | Empty message content | Ensure content is non-empty string or array |
| `tool_result: tool_use_id not found` | Mismatched tool ID | Copy `id` from the `tool_use` block exactly |

### 401 — `authentication_error`

```bash
# Verify your key is set and valid
echo $ANTHROPIC_API_KEY | head -c 15  # Should show: sk-ant-api03-...

# Test directly with curl
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":16,"messages":[{"role":"user","content":"hi"}]}'
```

### 403 — `permission_error`

API key lacks required permissions. Generate a new key at [console.anthropic.com](https://console.anthropic.com).

### 404 — `not_found_error`

Invalid endpoint or model. Check you're using `https://api.anthropic.com/v1/messages` and a valid model ID.

### 429 — `rate_limit_error`

```json
{"type": "error", "error": {"type": "rate_limit_error", "message": "Number of request tokens has exceeded your per-minute rate limit"}}
```

**Check headers for details:**
- `retry-after` — seconds to wait
- `anthropic-ratelimit-requests-limit` — RPM cap
- `anthropic-ratelimit-tokens-limit` — TPM cap
- `anthropic-ratelimit-tokens-remaining` — tokens left this window

**Fix:** The SDK handles 429 with automatic retry (configurable via `maxRetries`). For manual handling, see `anth-rate-limits`.

### 529 — `overloaded_error`

API is temporarily overloaded. Retry after 30-60 seconds. Not counted against rate limits.

### 500 — `api_error`

Internal server error. Retry with exponential backoff. If persistent, check [status.anthropic.com](https://status.anthropic.com).

## Quick Diagnostic Script

```bash
# 1. Check API status
curl -s https://status.anthropic.com/api/v2/status.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['description'])"

# 2. Verify key format
echo $ANTHROPIC_API_KEY | grep -qE '^sk-ant-api03-' && echo "Key format OK" || echo "Key format WRONG"

# 3. Test minimal request
curl -s -w "\nHTTP %{http_code}" https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":8,"messages":[{"role":"user","content":"1+1="}]}'
```

## SDK Error Handling

```python
import anthropic

try:
    message = client.messages.create(...)
except anthropic.AuthenticationError as e:
    print(f"Auth failed: {e.status_code}")
except anthropic.RateLimitError as e:
    print(f"Rate limited. Retry after: {e.response.headers.get('retry-after')}s")
except anthropic.BadRequestError as e:
    print(f"Invalid request: {e.message}")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
except anthropic.APIConnectionError:
    print("Network error — check connectivity")
```

## Resources

- [Error Types Reference](https://docs.anthropic.com/en/api/errors)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [API Status](https://status.anthropic.com)

## Next Steps

For comprehensive debugging, see `anth-debug-bundle`.
