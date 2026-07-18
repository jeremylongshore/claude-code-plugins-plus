# Groq Error Reference

Full per-status reference for Groq API errors — causes, exact error strings, and proven fixes. This is the deep companion to the `groq-common-errors` skill; SKILL.md summarizes the workflow and links here for the complete table.

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

## 401 — Authentication Error

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

## 429 — Rate Limit Exceeded

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

## 400 — Bad Request

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

## 413 — Request Too Large

```
Maximum context length is 131072 tokens. However, your messages resulted in 140000 tokens.
```

**Fix**: Reduce prompt size or split into smaller requests. All current Llama models have 128K context.

## 500 / 503 — Server Errors

```
Internal server error / Service temporarily unavailable
```

**Causes**: Groq infrastructure issue, model overloaded.
**Fix**: Retry with backoff, fall back to a different model, check [status.groq.com](https://status.groq.com).
