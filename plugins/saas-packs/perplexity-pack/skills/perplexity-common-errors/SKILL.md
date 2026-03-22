---
name: perplexity-common-errors
description: |
  Diagnose and fix Perplexity Sonar API errors and exceptions.
  Use when encountering Perplexity errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "perplexity error", "fix perplexity",
  "perplexity not working", "debug perplexity", "perplexity 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, debugging]

---
# Perplexity Common Errors

## Overview
Quick reference for the most common Perplexity Sonar API errors, their root causes, and fixes. All Perplexity errors follow the OpenAI error format since the API is OpenAI-compatible.

## Prerequisites
- `PERPLEXITY_API_KEY` environment variable set
- `curl` available for diagnostic commands

## Error Reference

### 401 Unauthorized — Invalid API Key
```json
{"error": {"message": "Invalid API key", "type": "authentication_error", "code": 401}}
```

**Causes:** Key missing, expired, revoked, or doesn't start with `pplx-`.

**Fix:**
```bash
set -euo pipefail
# Verify key is set and has correct prefix
echo "${PERPLEXITY_API_KEY:0:5}"  # Should print "pplx-"

# Test key directly
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions
# 200 = valid, 401 = invalid key
```

Regenerate at [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api).

---

### 429 Too Many Requests — Rate Limited
```json
{"error": {"message": "Rate limit exceeded", "type": "rate_limit_error", "code": 429}}
```

**Causes:** Exceeded requests per minute (RPM). Most tiers allow 50 RPM. Perplexity uses a leaky bucket algorithm.

**Fix:**
```typescript
async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.status !== 429 || i === maxRetries) throw err;
      const delay = Math.pow(2, i) * 1000 + Math.random() * 500;
      console.log(`Rate limited. Retrying in ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

See `perplexity-rate-limits` for queue-based solutions.

---

### 400 Bad Request — Invalid Model
```json
{"error": {"message": "Invalid model: gpt-4", "type": "invalid_request_error"}}
```

**Cause:** Using a non-Perplexity model name.

**Valid models:** `sonar`, `sonar-pro`, `sonar-reasoning-pro`, `sonar-deep-research`.

---

### 400 Bad Request — Invalid search_domain_filter
```json
{"error": {"message": "search_domain_filter must contain at most 20 domains"}}
```

**Cause:** Exceeding the 20-domain limit, or mixing allowlist (no prefix) with denylist (`-` prefix).

**Fix:** Use either allowlist OR denylist mode, not both:
```typescript
// Allowlist: only these domains
search_domain_filter: ["python.org", "docs.python.org"]

// Denylist: exclude these domains
search_domain_filter: ["-reddit.com", "-quora.com"]
```

---

### Empty Citations Array
Not an error, but a common surprise.

**Causes:** Query too abstract, non-factual question, or model couldn't find relevant sources.

**Fix:**
```typescript
// BAD: abstract query yields no citations
"Tell me about technology"

// GOOD: specific factual query
"What are the key features of TypeScript 5.5 released in 2025?"
```

Use `sonar-pro` for more citations (2x average citation count vs `sonar`).

---

### Timeout / Hanging Request
**Causes:** Complex query with `sonar-pro` or `sonar-deep-research`. Sonar: 1-3s typical. Sonar-pro: 3-8s. Deep research: 10-60s.

**Fix:**
```typescript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 15000);

try {
  const response = await perplexity.chat.completions.create(
    { model: "sonar", messages: [{ role: "user", content: query }] },
    { signal: controller.signal }
  );
  return response;
} finally {
  clearTimeout(timeout);
}
```

---

### 402 Payment Required — No Credits
```json
{"error": {"message": "Insufficient credits", "type": "billing_error"}}
```

**Cause:** Account has no API credits remaining.

**Fix:** Add credits at [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api).

## Diagnostic Commands
```bash
set -euo pipefail
# Quick API health check
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions

# Check if key env var is set
env | grep PERPLEXITY

# Test DNS resolution
dig api.perplexity.ai +short
```

## Error Handling
| HTTP Code | Error Type | Retry? | Action |
|-----------|-----------|--------|--------|
| 400 | `invalid_request_error` | No | Fix request parameters |
| 401 | `authentication_error` | No | Regenerate API key |
| 402 | `billing_error` | No | Add credits |
| 429 | `rate_limit_error` | Yes | Exponential backoff |
| 500+ | `server_error` | Yes | Retry after 2-5 seconds |

## Output
- Identified error cause from HTTP status and error type
- Applied fix or workaround
- Verified resolution with diagnostic commands

## Resources
- [Perplexity Error Handling Guide](https://docs.perplexity.ai/guides/perplexity-sdk-error-handling)
- [API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)

## Next Steps
For comprehensive debugging, see `perplexity-debug-bundle`.
