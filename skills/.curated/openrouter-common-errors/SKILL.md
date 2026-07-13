---
name: openrouter-common-errors
description: 'Diagnose and fix common OpenRouter API errors. Use when encountering
  error codes, unexpected failures, or debugging API responses. Triggers: ''openrouter
  error'', ''openrouter 401'', ''openrouter 429'', ''openrouter 402'', ''fix openrouter''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(node:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- errors
- debugging
- troubleshooting
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Common Errors

## Overview

OpenRouter returns standard HTTP error codes plus OpenRouter-specific error codes in the response body. The most common: 401 (auth), 402 (credits), 429 (rate limit), 400 (bad request), and 5xx (upstream provider errors). Each error includes a `code` field and a human-readable `message`. This skill covers every common error, its root cause, and the exact fix.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- `curl` and `jq` to run the Diagnostic Script
- Python 3.8+ with the OpenAI SDK for the categorized error handler; Node.js 18+ for the TypeScript typed-error classifier in the references
- The `requests` package if you use the Prevention Middleware's pre-flight model check

## Instructions

1. Identify the failure by HTTP status and `code` using the Complete Error Reference table (400/401/402/403/408/429/5xx each map to a specific fix).
2. Inspect the body per Error Response Format — `error.code`, `error.message`, and `error.metadata.provider_name` tell you whether OpenRouter or the upstream provider failed.
3. Run the Diagnostic Script: it checks auth via `GET /api/v1/auth/key`, computes remaining credits, verifies the model exists in `/api/v1/models`, and fires a minimal 1-token completion.
4. Wrap production calls with `safe_completion()` from Python Error Handler — `max_retries=3` auto-retries 429 and 5xx, and each exception class raises with its exact remedy.
5. Add `validate_before_send()` from Prevention Middleware to catch bad model IDs (with suggestions), malformed messages, and context overflows before spending money on a 400.
6. If errors persist across retries and providers, check [status.openrouter.ai](https://status.openrouter.ai) per the Error Handling table.

## Complete Error Reference

| HTTP | Error Code | Cause | Fix |
|------|-----------|-------|-----|
| 400 | `bad_request` | Malformed request body | Validate `messages` array format; ensure model ID includes provider prefix |
| 400 | `invalid_model` | Model ID not found | Check model exists: `curl -s https://openrouter.ai/api/v1/models \| jq '.data[].id'` |
| 400 | `context_length_exceeded` | Prompt + max_tokens > model limit | Reduce prompt size or use a larger-context model |
| 400 | `invalid_tool_schema` | Tool definition has unsupported types | Use basic JSON Schema types only (string, number, boolean, object, array) |
| 401 | `invalid_api_key` | Key malformed, revoked, or wrong | Regenerate at [openrouter.ai/keys](https://openrouter.ai/keys); key must start with `sk-or-v1-` |
| 401 | `missing_api_key` | No `Authorization` header | Add `Authorization: Bearer sk-or-v1-...` header |
| 402 | `insufficient_credits` | Credit balance is zero | Top up at [openrouter.ai/credits](https://openrouter.ai/credits) |
| 402 | `credit_limit_reached` | Per-key credit limit hit | Increase key limit in dashboard or create new key |
| 403 | `key_disabled` | Key was disabled by admin | Re-enable in dashboard or create new key |
| 408 | `request_timeout` | Model took too long | Reduce max_tokens; use streaming; try faster model |
| 429 | `rate_limit_exceeded` | Too many requests per interval | SDK auto-retries; increase `max_retries`; use multiple keys |
| 502 | `provider_error` | Upstream provider returned error | Retry with backoff; try different provider via `provider.order` |
| 503 | `model_unavailable` | Model temporarily offline | Use fallback models; check [status.openrouter.ai](https://status.openrouter.ai) |

## Error Response Format

```json
{
  "error": {
    "code": 401,
    "message": "Invalid API key. Please check your API key and try again.",
    "metadata": {
      "provider_name": "Anthropic",
      "raw": "..."
    }
  }
}
```

## Diagnostic Script

```bash
#!/bin/bash
echo "=== OpenRouter Error Diagnostics ==="

# 1. Test authentication
echo -n "1. Auth: "
AUTH=$(curl -s -o /dev/null -w "%{http_code}" \
  https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY")
[ "$AUTH" = "200" ] && echo "OK" || echo "FAIL (HTTP $AUTH)"

# 2. Check credit balance
echo -n "2. Credits: "
CREDITS=$(curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | \
  jq -r '(.data.limit // 0) - .data.usage')
echo "\$$CREDITS remaining"

# 3. Test model availability
echo -n "3. Model: "
MODEL="openai/gpt-4o-mini"
EXISTS=$(curl -s https://openrouter.ai/api/v1/models | \
  jq --arg m "$MODEL" '[.data[] | select(.id == $m)] | length')
[ "$EXISTS" -gt 0 ] && echo "$MODEL available" || echo "$MODEL NOT FOUND"

# 4. Test a minimal request
echo -n "4. Request: "
RESP=$(curl -s -w "\n%{http_code}" \
  https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}],"max_tokens":1}')
HTTP=$(echo "$RESP" | tail -1)
[ "$HTTP" = "200" ] && echo "OK" || echo "FAIL (HTTP $HTTP)"
```

## Python Error Handler

```python
import os
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, BadRequestError, APITimeoutError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_retries=3,  # Auto-retry 429 and 5xx
    timeout=30.0,
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def safe_completion(messages, model="openai/gpt-4o-mini", **kwargs):
    """Completion with categorized error handling."""
    try:
        return client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
    except AuthenticationError as e:
        # 401: Bad or missing API key
        raise SystemExit(f"AUTH ERROR: Check OPENROUTER_API_KEY. {e}")
    except BadRequestError as e:
        # 400: Bad model ID, invalid params, context too long
        if "context_length" in str(e):
            raise ValueError(f"Prompt too long for {model}. Trim or use larger-context model.")
        raise ValueError(f"Bad request: {e}")
    except RateLimitError:
        # 429: SDK already retried max_retries times
        raise RuntimeError("Rate limited after all retries. Wait or use more API keys.")
    except APITimeoutError:
        # Timeout: model too slow
        raise TimeoutError(f"Model {model} timed out. Try streaming or a faster model.")
    except APIError as e:
        # 402, 5xx, other
        if e.status_code == 402:
            raise RuntimeError("Insufficient credits. Top up at openrouter.ai/credits")
        raise RuntimeError(f"API error {e.status_code}: {e}")
```

## Prevention Middleware

```python
import requests

def validate_before_send(model: str, messages: list, max_tokens: int = 1024):
    """Pre-flight validation to catch common mistakes before API call."""
    errors = []

    # Check model exists
    models = requests.get("https://openrouter.ai/api/v1/models").json()["data"]
    model_ids = {m["id"] for m in models}
    if model not in model_ids:
        # Try to suggest correct ID
        prefix = model.split("/")[0] if "/" in model else ""
        suggestions = [m for m in model_ids if prefix and m.startswith(prefix)][:3]
        errors.append(f"Model '{model}' not found. Did you mean: {suggestions}")

    # Check messages format
    if not messages or not isinstance(messages, list):
        errors.append("messages must be a non-empty list")
    for msg in messages:
        if "role" not in msg or "content" not in msg:
            errors.append(f"Each message needs 'role' and 'content': {msg}")

    # Estimate context usage
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    est_tokens = total_chars // 4
    model_info = next((m for m in models if m["id"] == model), None)
    if model_info:
        ctx_limit = model_info["context_length"]
        if est_tokens + max_tokens > ctx_limit:
            errors.append(f"Estimated {est_tokens} + {max_tokens} max_tokens > {ctx_limit} context limit")

    if errors:
        raise ValueError("Pre-flight validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
```

## Output

- A four-line diagnostic report: auth OK/FAIL, dollars of credit remaining, model availability in `/api/v1/models`, and the HTTP status of a minimal live request
- Categorized exceptions from `safe_completion()` — auth failures exit pointing at the key, 402s point at credit top-up, context overflows raise `ValueError` naming the model to trim for
- Pre-flight `ValueError`s from `validate_before_send()` listing every problem found (unknown model with suggested IDs, missing `role`/`content` fields, estimated-token overflow) before any API call is made

## Examples

A healthy integration produces this from the Diagnostic Script:

```text
=== OpenRouter Error Diagnostics ===
1. Auth: OK
2. Credits: $46.58 remaining
3. Model: openai/gpt-4o-mini available
4. Request: OK
```

Any FAIL line maps straight to a row in the Complete Error Reference table — e.g. `1. Auth: FAIL (HTTP 401)` means regenerating the key at openrouter.ai/keys. More worked examples: `references/examples.md`.

## Error Handling

| Scenario | SDK Behavior | Your Action |
|----------|-------------|-------------|
| 429 rate limit | Auto-retries with backoff | Increase `max_retries` or add keys |
| 5xx server error | Auto-retries with backoff | Increase `max_retries`; add fallback models |
| 401 auth error | Fails immediately (no retry) | Fix API key and retry |
| 400 bad request | Fails immediately (no retry) | Fix request parameters |
| 402 no credits | Fails immediately (no retry) | Top up credits |

## Enterprise Considerations

- The OpenAI SDK handles 429 and 5xx retries automatically -- configure `max_retries` (default 2, recommend 3-5)
- Implement pre-flight validation to catch 400 errors before making API calls (saves money and time)
- Log error codes and rates to detect systematic issues (e.g., provider outages show as 502 spike)
- Build a status dashboard that checks both your error rates and [status.openrouter.ai](https://status.openrouter.ai)
- For 402 errors, implement credit balance monitoring with alerts at 20% remaining

## References

- Examples | Errors
- Error Codes | [Status](https://status.openrouter.ai)
