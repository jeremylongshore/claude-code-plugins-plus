---
name: groq-common-errors
description: |
  Diagnose and fix Groq API errors with real error codes and solutions.
  Use when encountering Groq errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "groq error", "fix groq",
  "groq not working", "debug groq", "groq 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, debugging]

---
# Groq Common Errors

## Overview
Comprehensive reference for Groq API error codes, their root causes, and proven fixes. Groq returns standard HTTP status codes with structured error bodies and rate-limit headers.

## Error Response Format
```json
{
  "error": {
    "message": "Rate limit reached for model `llama-3.3-70b-versatile`...",
    "type": "tokens",
    "code": "rate_limit_exceeded"
  }
}
```

## Quick Diagnostic
```bash
set -euo pipefail
# 1. Verify API key is valid
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data | length'

# 2. Check specific model availability
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data[].id' | sort

# 3. Test a minimal completion
curl -s https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' | jq .
```

## Error Reference

### 401 — Authentication Error
```
Authentication error: Invalid API key provided
```
**Causes**: Key missing, revoked, or malformed.
**Fix**:
```bash
# Verify key is set and starts with gsk_
echo "${GROQ_API_KEY:0:4}"  # Should print "gsk_"

# Test key directly
curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
# Should return 200
```

### 429 — Rate Limit Exceeded
```
Rate limit reached for model `llama-3.3-70b-versatile` in organization `org_xxx`
on tokens per minute (TPM): Limit 6000, Used 5800, Requested 500.
```
**Causes**: RPM (requests/min), TPM (tokens/min), or RPD (requests/day) limit hit.

**Rate limit headers returned**:
| Header | Description |
|--------|-------------|
| `retry-after` | Seconds to wait before retrying |
| `x-ratelimit-limit-requests` | Max requests per window |
| `x-ratelimit-limit-tokens` | Max tokens per window |
| `x-ratelimit-remaining-requests` | Requests remaining |
| `x-ratelimit-remaining-tokens` | Tokens remaining |
| `x-ratelimit-reset-requests` | When request limit resets |
| `x-ratelimit-reset-tokens` | When token limit resets |

**Fix**:
```typescript
import Groq from "groq-sdk";

async function handleRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    if (err instanceof Groq.APIError && err.status === 429) {
      const retryAfter = parseInt(err.headers?.["retry-after"] || "10");
      console.warn(`Rate limited. Waiting ${retryAfter}s...`);
      await new Promise((r) => setTimeout(r, retryAfter * 1000));
      return fn(); // Single retry
    }
    throw err;
  }
}
```

### 400 — Bad Request
```
Invalid parameter: model 'mixtral-8x7b-32768' is not available
```
**Causes**: Deprecated model ID, invalid parameters, or schema violation.

**Common deprecated model IDs**:
| Deprecated | Replacement |
|-----------|-------------|
| `mixtral-8x7b-32768` | `llama-3.1-8b-instant` or `llama-3.3-70b-versatile` |
| `gemma2-9b-it` | `llama-3.1-8b-instant` |
| `llama-3.1-70b-versatile` | `llama-3.3-70b-versatile` |

**Fix**: Check current models at [console.groq.com/docs/models](https://console.groq.com/docs/models) or call `GET /openai/v1/models`.

### 413 — Request Too Large
```
Maximum context length is 131072 tokens. However, your messages resulted in 140000 tokens.
```
**Fix**: Reduce prompt size or split into smaller requests. All current Llama models have 128K context.

### 500 / 503 — Server Errors
```
Internal server error / Service temporarily unavailable
```
**Causes**: Groq infrastructure issue, model overloaded.
**Fix**: Retry with backoff, fall back to a different model, check [status.groq.com](https://status.groq.com).

### SDK-Specific Errors

**TypeScript**:
```typescript
import Groq from "groq-sdk";

try {
  await groq.chat.completions.create({ /* ... */ });
} catch (err) {
  if (err instanceof Groq.APIError) {
    console.error(`Status: ${err.status}, Message: ${err.message}`);
  } else if (err instanceof Groq.APIConnectionError) {
    console.error("Network error:", err.message);
  } else if (err instanceof Groq.RateLimitError) {
    console.error("Rate limited:", err.message);
  } else if (err instanceof Groq.AuthenticationError) {
    console.error("Auth failed:", err.message);
  }
}
```

**Python**:
```python
from groq import Groq, APIError, RateLimitError, AuthenticationError

try:
    client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
except AuthenticationError as e:
    print(f"Auth error: {e.message}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Escalation Path
1. Check [status.groq.com](https://status.groq.com) for ongoing incidents
2. Collect request ID from error response (`x-request-id` header)
3. Run `groq-debug-bundle` skill to gather diagnostics
4. Contact Groq support with request ID and debug bundle

## Resources
- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)
- [Groq Status Page](https://status.groq.com)

## Next Steps
For comprehensive debugging, see `groq-debug-bundle`.
