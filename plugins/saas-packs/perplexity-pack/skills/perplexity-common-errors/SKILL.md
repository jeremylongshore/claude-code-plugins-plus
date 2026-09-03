---
name: perplexity-common-errors
description: 'Diagnose and fix Perplexity Sonar API errors and exceptions.

  Use when encountering Perplexity errors, debugging failed requests,

  or troubleshooting integration issues.

  Trigger with phrases like "perplexity error", "fix perplexity",

  "perplexity not working", "debug perplexity", "perplexity 429".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(jq:*)
version: 1.12.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- perplexity
- debugging
compatibility: Designed for Claude Code
---
# Perplexity Common Errors

## Overview

Quick reference for common Perplexity Sonar API failures, their likely causes, and safe recovery paths. The Sonar API supports the OpenAI Chat Completions format, while the official Perplexity SDK exposes typed error classes; callers must still classify failures by observed status and response schema.

## Prerequisites

- `PERPLEXITY_API_KEY` environment variable set
- `curl` and `jq` available for metadata-only diagnostics
- A synthetic, non-customer prompt approved for health checks

## Instructions

1. Use `Read` and `Grep` on approved application telemetry to capture the HTTP status, provider request ID, model, attempt count, and latency. Never record authorization headers, key fragments, prompts, answers, or raw error bodies.
2. Classify the failure before retrying: request/authentication/billing failures are terminal; throttling, connection failures, and provider 5xx responses may be retried within a bounded budget.
3. Reproduce once with the safe probe below and the fixed `https://api.perplexity.ai` origin. A malformed 200 response is a failure, not a success.
4. Correct the request or operating condition, then rerun the same probe. Preserve only the metadata receipt.

## Error Reference

### 401 Unauthorized — Invalid API Key

```json
{"error": {"message": "Invalid API key", "type": "authentication_error", "code": 401}}
```

**Causes:** Key missing, expired, revoked, or loaded from the wrong secret scope.

**Fix:**

```bash
set -euo pipefail
test -n "${PERPLEXITY_API_KEY:-}" || {
  echo "PERPLEXITY_API_KEY is not set" >&2
  exit 1
}

response="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}' \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"model":"sonar","messages":[{"role":"user","content":"Reply with ready."}],"max_tokens":8}' \
  https://api.perplexity.ai/chat/completions)"
http_status="${response##*$'\n'}"
body="${response%$'\n'*}"

case "${http_status}" in
  200)
    printf '%s\n' "${body}" | jq -er '
      .choices[0].finish_reason
      | select(type == "string" and length > 0)
    ' >/dev/null
    printf 'Perplexity probe OK (HTTP %s)\n' "${http_status}"
    ;;
  401|402|429)
    echo "Perplexity probe failed with HTTP ${http_status}; response body suppressed." >&2
    exit 1
    ;;
  *)
    echo "Perplexity probe failed with HTTP ${http_status}." >&2
    exit 1
    ;;
esac
```

Regenerate at [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api).

---

### 429 Too Many Requests — Rate Limited

```json
{"error": {"message": "Rate limit exceeded", "type": "rate_limit_error", "code": 429}}
```

**Causes:** The active project, API, or model exceeded its current account-specific limit. Do not assume one universal requests-per-minute value.

**Fix:**

```typescript
async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.status !== 429 || i === maxRetries) throw err;
      const retryAfter = Number(err.headers?.get?.("retry-after"));
      const exponential = Math.min(2 ** i * 1000, 8_000);
      const delay = Number.isFinite(retryAfter)
        ? Math.min(retryAfter * 1000, 30_000)
        : exponential + Math.random() * 250;
      console.warn(`Rate limited; retry ${i + 1}/${maxRetries} after a bounded delay.`);
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

If citations are required, validate the `citations` or `search_results` field and fail or degrade explicitly when it is absent.

---

### Timeout / Hanging Request

**Causes:** Complex retrieval, provider congestion, or a caller timeout below the measured latency envelope.

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
# Presence only: never print the variable, prefix, length, or environment.
test -n "${PERPLEXITY_API_KEY:-}" && printf '%s\n' "credential configured"
```

## Error Handling

| HTTP Code | Error Type | Retry? | Action |
|-----------|-----------|--------|--------|
| 400 | `invalid_request_error` | No | Fix request parameters |
| 401 | `authentication_error` | No | Regenerate API key |
| 402 | `billing_error` | No | Add credits |
| 429 | `rate_limit_error` | Yes | Exponential backoff |
| 500+ | `server_error` | Yes | Use bounded exponential delay and total deadline |

## Examples

### Authentication failure

The probe returns 401 with no body printed. Confirm the workload references the intended secret name and environment, rotate the credential through the approved secret manager if necessary, and rerun the probe. Record only the 401-to-200 transition and provider request IDs.

### Throttling burst

When a bounded worker receives 429, pause new work, honor a valid `Retry-After` value within the configured ceiling, and retry no more than the operation budget. If the budget expires, enqueue the request or return an explicit degraded response instead of starting an unbounded retry storm.

## Output

- Identified error cause from HTTP status and error type
- Applied fix or workaround
- Verified resolution with diagnostic commands

## Resources

- [Perplexity SDK Error Handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)
- [Failure-classification reference](references/error-classification.md)

## Next Steps

For comprehensive debugging, see `perplexity-debug-bundle`.
