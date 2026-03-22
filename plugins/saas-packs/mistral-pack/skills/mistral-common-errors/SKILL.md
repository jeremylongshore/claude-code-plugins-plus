---
name: mistral-common-errors
description: |
  Diagnose and fix Mistral AI common errors and exceptions.
  Use when encountering Mistral errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "mistral error", "fix mistral",
  "mistral not working", "debug mistral".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, debugging]

---
# Mistral AI Common Errors

## Overview
Quick reference for diagnosing and fixing Mistral AI API errors. Covers HTTP status codes, SDK-specific issues, streaming failures, and tool calling problems with real solutions.

## Prerequisites
- Mistral AI SDK installed
- `MISTRAL_API_KEY` configured
- Access to application logs

## Instructions

### Step 1: Quick Diagnostic

```bash
set -euo pipefail
# Test API connectivity and auth
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models | jq '.data[].id' 2>/dev/null || echo "FAILED"

# Check env
echo "Key set: ${MISTRAL_API_KEY:+yes}"
echo "Key length: ${#MISTRAL_API_KEY}"
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

#### 413 / Context Length Exceeded
```
Error: Maximum context length exceeded
```

**Fix:** Trim conversation history, keeping system message:
```typescript
function trimToFit(messages: any[], maxChars = 100_000): any[] {
  const system = messages.find(m => m.role === 'system');
  const rest = messages.filter(m => m.role !== 'system');
  const kept: any[] = system ? [system] : [];
  let chars = system?.content?.length ?? 0;

  // Keep most recent messages that fit
  for (let i = rest.length - 1; i >= 0; i--) {
    const msgChars = JSON.stringify(rest[i]).length;
    if (chars + msgChars > maxChars) break;
    chars += msgChars;
    kept.splice(system ? 1 : 0, 0, rest[i]);
  }
  return kept;
}
```

---

#### 500/503 Server Error
```
Error: Internal server error
```

**Causes:** Mistral service issue (temporary).

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
      if (error.status >= 500) {
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
| `413` | Context overflow | Trim conversation history |
| `5xx` | Service error | Retry with circuit breaker |
| `ERR_REQUIRE_ESM` | CJS import | Use ESM `import` syntax |

## Resources
- [Mistral API Reference](https://docs.mistral.ai/api/)
- [Rate Limits & Tiers](https://docs.mistral.ai/deployment/ai-studio/tier/)
- [Status Page](https://status.mistral.ai/)
- [Discord Community](https://discord.gg/mistralai)

## Next Steps
For comprehensive debugging, see `mistral-debug-bundle`.
