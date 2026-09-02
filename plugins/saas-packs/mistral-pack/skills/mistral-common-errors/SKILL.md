---
name: mistral-common-errors
description: 'Diagnose and fix Mistral AI common errors and exceptions.

  Use when encountering Mistral errors, debugging failed requests,

  or troubleshooting integration issues.

  Trigger with phrases like "mistral error", "fix mistral",

  "mistral not working", "debug mistral".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.12.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mistral
- debugging
compatibility: Designed for Claude Code
---
# Mistral AI Common Errors

## Overview

Quick reference for diagnosing and fixing Mistral AI API errors. Covers HTTP status codes, SDK-specific issues, streaming failures, and tool calling problems with real solutions.

## Prerequisites

- Mistral AI SDK installed
- `MISTRAL_API_KEY` configured
- Read-only access to application logs and configuration
- `curl` and `jq` available for the diagnostic probe
- Access to the secret manager if a credential must be rotated

## Instructions

### Step 1: Quick Diagnostic

Use `Read` for the relevant configuration and log files, then `Grep` for the exact
HTTP status, request ID, model name, and error `code`. Never print, paste, or store
the API key while collecting evidence.

```bash
set -euo pipefail
# Check presence without revealing key material or key metadata
test -n "${MISTRAL_API_KEY:-}" || {
  echo "MISTRAL_API_KEY is not set" >&2
  exit 1
}

# Test API connectivity and auth
curl -sS -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models | jq '.data[].id' 2>/dev/null || echo "FAILED"
```

### Step 2: Error Reference

---

#### 401 Unauthorized

```
Error: Authentication failed. Invalid API key.
```

**Causes:** Key missing, expired, revoked, or wrong workspace.

**Fix:**

```typescript
const apiKey = process.env.MISTRAL_API_KEY;
if (!apiKey) throw new Error('MISTRAL_API_KEY is not set');

// Test the key
const client = new Mistral({ apiKey });
try {
  await client.models.list();
} catch (e: any) {
  if (e.status === 401) {
    console.error('API key invalid — regenerate at console.mistral.ai');
  }
}
```

**Verify manually:**

```bash
set -euo pipefail
curl -H "Authorization: Bearer ${MISTRAL_API_KEY}" https://api.mistral.ai/v1/models
```

---

#### 429 Too Many Requests

```
Error: Rate limit exceeded. Retry-After: 60
```

**Causes:** Exceeded RPM (requests/min) or TPM (tokens/min) for your tier.

**Fix:**

```typescript
async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error.status !== 429 || i === maxRetries) throw error;
      const wait = Math.min(2 ** i * 1000, 60_000);
      console.warn(`Rate limited, retrying in ${wait}ms...`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Check your limits:** Visit [console.mistral.ai/limits](https://admin.mistral.ai/plateforme/limits) for workspace RPM/TPM caps.

---

#### 400 Bad Request — Invalid Model

```
{"message": "Unknown model: mistral-ultra"}
```

**Fix:** Use valid model IDs:

```typescript
const VALID_MODELS = [
  'mistral-large-latest',
  'mistral-small-latest',
  'codestral-latest',
  'pixtral-large-latest',
  'mistral-embed',
  'mistral-moderation-latest',
] as const;
```

**List available models dynamically:**

```bash
set -euo pipefail
curl -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models | jq -r '.data[].id' | sort
```

---

#### 400 Bad Request — Invalid Messages

```
{"message": "messages must be a non-empty array"}
```

**Fix:** Validate message structure before sending:

```typescript
function validateMessages(messages: any[]): void {
  if (!messages?.length) throw new Error('Messages array empty');
  const validRoles = ['system', 'user', 'assistant', 'tool'];
  for (const msg of messages) {
    if (!validRoles.includes(msg.role)) {
      throw new Error(`Invalid role: "${msg.role}"`);
    }
    if (!msg.content && !msg.toolCalls) {
      throw new Error(`Message with role "${msg.role}" has no content`);
    }
  }
}
```

---

#### 400 Bad Request — Tool Call Errors

```
{"message": "tool_call_id is required for tool messages"}
```

**Fix:** Every tool result must include the matching `toolCallId`:

```typescript
// After receiving tool_calls from the model
for (const call of response.choices[0].message.toolCalls) {
  const result = await executeFunction(call.function.name, call.function.arguments);
  messages.push({
    role: 'tool',
    name: call.function.name,
    content: JSON.stringify(result),
    toolCallId: call.id,  // REQUIRED — must match call.id
  });
}
```

---

#### 400 Bad Request — Context Window Exceeded

```
Error: Maximum context length exceeded
```

**Fix:** Determine the selected model's current context window from its model card,
count both input and requested output tokens, and trim conversation history while
preserving the system message:

```typescript
function trimToFit(
  messages: any[],
  countTokens: (candidate: any[]) => number,
  maxContextTokens: number,
  reservedOutputTokens: number,
): any[] {
  const system = messages.find(m => m.role === 'system');
  const rest = messages.filter(m => m.role !== 'system');
  const kept: any[] = system ? [system] : [];
  const inputBudget = maxContextTokens - reservedOutputTokens;

  // Keep the newest complete messages that fit the tokenizer-backed budget.
  for (let i = rest.length - 1; i >= 0; i--) {
    const insertAt = system ? 1 : 0;
    const candidate = [...kept];
    candidate.splice(insertAt, 0, rest[i]);
    if (countTokens(candidate) > inputBudget) break;
    kept.splice(insertAt, 0, rest[i]);
  }
  return kept;
}
```

---

#### 500/502/503/504 Server Error

```
Error: Internal server error
```

**Causes:** A transient Mistral service or gateway issue.

**Fix:**

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold = 5;
  private readonly resetMs = 60_000;

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.failures >= this.threshold) {
      if (Date.now() - this.lastFailure < this.resetMs) {
        throw new Error('Circuit breaker open — Mistral service unavailable');
      }
      this.failures = 0; // Reset after timeout
    }
    try {
      const result = await fn();
      this.failures = 0;
      return result;
    } catch (error: any) {
      if ([500, 502, 503, 504].includes(error.status)) {
        this.failures++;
        this.lastFailure = Date.now();
      }
      throw error;
    }
  }
}
```

---

#### ERR_REQUIRE_ESM (Node.js)

```
Error [ERR_REQUIRE_ESM]: require() of ES Module not supported
```

**Cause:** `@mistralai/mistralai` is ESM-only since v1.x.

**Fix:** Either use `import` syntax (recommended) or dynamic import:

```typescript
// Option 1: Convert to ESM
// package.json: "type": "module"
import { Mistral } from '@mistralai/mistralai';

// Option 2: Dynamic import in CJS
const { Mistral } = await import('@mistralai/mistralai');
```

---

#### Network Timeout

```
Error: Request timeout after 30000ms
```

**Fix:**

```typescript
const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  timeoutMs: 60_000, // Increase for long completions
});

// For streaming, the timeout applies to initial connection
// Individual chunks have no timeout
```

## Escalation Path

1. Collect evidence with `mistral-debug-bundle`
2. Check [status.mistral.ai](https://status.mistral.ai/)
3. Contact support via [Discord](https://discord.gg/mistralai) or console.mistral.ai

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401` | Auth failure | Regenerate key at console.mistral.ai |
| `429` | Rate limit | Backoff + check tier limits |
| `400` | Bad params | Validate model, messages, tools |
| `400` context-window error | Input plus requested output exceeds the model limit | Count tokens and trim conversation history |
| `5xx` | Service error | Retry with circuit breaker |
| `ERR_REQUIRE_ESM` | CJS import | Use ESM `import` syntax |

For the evidence to collect and the safe decision boundary for each class, read
[the error triage playbook](references/error-triage-playbook.md).

## Output

Return a redacted diagnostic report with these fields:

```text
Mistral incident: <short symptom>
Observed at: <UTC timestamp>
Scope: <endpoint, model, environment, affected request percentage>
Evidence: <HTTP status, error type/code, request ID; never credentials>
Classification: <caller defect | auth | authorization | capacity | transient provider | network>
Action taken: <one reversible mitigation>
Verification: <probe or application check and result>
Next action: <owner and trigger, or "none — resolved">
```

Do not claim resolution from one successful retry. Require the application's normal
health signal to recover and a short observation window with no repeat of the same
error class.

## Examples

### Authentication failure

Input evidence: production requests return `401 authentication_error`; the same
key fails a redacted `/v1/models` probe. Classify this as authentication, rotate the
credential through the secret manager, restart only the consumers that need the new
version, and verify with both the probe and application telemetry. The report records
the secret version identifier, never the key value or prefix.

### Rate-limit saturation

Input evidence: a burst produces `429 rate_limit_error` while ordinary traffic is
healthy. Preserve the response request ID and rate-limit headers, reduce concurrency,
honor server retry guidance, and use exponential backoff with jitter. Escalate for a
limit increase only after comparing observed requests and tokens against the current
organization limits.

## Resources

- [Mistral API Reference](https://docs.mistral.ai/api/)
- [Mistral error glossary](https://docs.mistral.ai/resources/error-glossary)
- [Usage and limits](https://docs.mistral.ai/admin/billing-usage/usage-limits)
- [Known limitations](https://docs.mistral.ai/resources/known-limitations)
- [Status Page](https://status.mistral.ai/)

## Next Steps

For comprehensive debugging, see `mistral-debug-bundle`. For an active outage with
user impact, switch to `mistral-incident-runbook` after preserving the redacted
request evidence.
