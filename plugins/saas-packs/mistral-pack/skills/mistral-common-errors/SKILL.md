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
---
# Mistral AI Common Errors

## Overview
Quick reference for the most common Mistral AI errors and their solutions.

## Prerequisites
- Mistral AI SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message, status code, and request ID in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

### 401 Unauthorized - Authentication Failed
**Error Message:**
```
Error: Authentication failed. Invalid API key.
Status: 401  # HTTP 401 Unauthorized
```

**Cause:** API key is missing, expired, or invalid.

**Solution:**
```bash
set -euo pipefail
# Verify API key is set
echo $MISTRAL_API_KEY

# Test API key
curl -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  https://api.mistral.ai/v1/models
```

**Code Fix:**
```typescript
// Ensure API key is loaded
const apiKey = process.env.MISTRAL_API_KEY;
if (!apiKey) {
  throw new Error('MISTRAL_API_KEY is not set');
}
const client = new Mistral({ apiKey });
```

---

### 429 Too Many Requests - Rate Limited
**Error Message:**
```
Error: Rate limit exceeded. Please retry after X seconds.
Status: 429  # HTTP 429 Too Many Requests
Headers: Retry-After: 60
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `mistral-rate-limits` skill.

```typescript
// Quick fix: Add delay and retry
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error.status === 429 && i < maxRetries - 1) {  # HTTP 429 Too Many Requests
        const retryAfter = parseInt(error.headers?.['retry-after'] || '60');
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));  # 1000: 1 second in ms
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

### 400 Bad Request - Invalid Parameters
**Error Message:**
```
Error: Invalid request. Check your parameters.
Status: 400  # HTTP 400 Bad Request
{"message": "Invalid model: mistral-ultra"}
```

**Cause:** Invalid model name, malformed messages, or incorrect parameters.

**Solution:**
```typescript
// Valid model names
const VALID_MODELS = [
  'mistral-large-latest',
  'mistral-medium-latest',  // Deprecated - use small or large
  'mistral-small-latest',
  'open-mistral-7b',
  'open-mixtral-8x7b',
  'mistral-embed',
] as const;

// Validate before request
function validateRequest(model: string, messages: any[]) {
  if (!VALID_MODELS.includes(model as any)) {
    throw new Error(`Invalid model: ${model}`);
  }
  if (!messages || messages.length === 0) {
    throw new Error('Messages array cannot be empty');
  }
  for (const msg of messages) {
    if (!['system', 'user', 'assistant', 'tool'].includes(msg.role)) {
      throw new Error(`Invalid role: ${msg.role}`);
    }
  }
}
```

---

### 413 Payload Too Large - Context Exceeded
**Error Message:**
```
Error: Request too large. Maximum context length exceeded.
Status: 413  # 413 = configured value
```

**Cause:** Too many tokens in the request.

**Solution:**
```typescript
// Truncate conversation history
function truncateMessages(messages: Message[], maxTokens = 30000): Message[] {  # 30000: 30 seconds in ms
  // Keep system message
  const systemMsg = messages.find(m => m.role === 'system');
  const otherMsgs = messages.filter(m => m.role !== 'system');

  // Estimate ~4 chars per token
  let tokenEstimate = systemMsg ? systemMsg.content.length / 4 : 0;
  const truncated: Message[] = systemMsg ? [systemMsg] : [];

  // Add messages from most recent
  for (let i = otherMsgs.length - 1; i >= 0; i--) {
    const msgTokens = otherMsgs[i].content.length / 4;
    if (tokenEstimate + msgTokens > maxTokens) break;
    tokenEstimate += msgTokens;
    truncated.unshift(otherMsgs[i]);
  }

  return truncated;
}
```

---

### 500/503 Server Error - Mistral Service Issue
**Error Message:**
```
Error: Internal server error
Status: 500/503  # 503: HTTP 500 Internal Server Error
```

**Cause:** Mistral AI service experiencing issues.

**Solution:**
```bash
set -euo pipefail
# Check Mistral status
curl -s https://status.mistral.ai/ | head -20

# Implement circuit breaker
```

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure?: Date;
  private readonly threshold = 5;
  private readonly resetTimeout = 60000; // 1 minute  # 60000: 1 minute in ms

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.isOpen()) {
      throw new Error('Circuit breaker is open');
    }

    try {
      const result = await fn();
      this.failures = 0;
      return result;
    } catch (error: any) {
      if (error.status >= 500) {  # HTTP 500 Internal Server Error
        this.failures++;
        this.lastFailure = new Date();
      }
      throw error;
    }
  }

  private isOpen(): boolean {
    if (this.failures < this.threshold) return false;
    const elapsed = Date.now() - (this.lastFailure?.getTime() || 0);
    return elapsed < this.resetTimeout;
  }
}
```

---

### Network Timeout
**Error Message:**
```
Error: Request timeout after 30000ms
```

**Cause:** Network connectivity or server latency issues.

**Solution:**
```typescript
// Increase timeout
const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  timeout: 60000, // 60 seconds  # 60000: 1 minute in ms
});

// For streaming, use longer timeout
const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  timeout: 120000, // 2 minutes for long responses  # 120000 = configured value
});
```

---

### Invalid Tool/Function Schema
**Error Message:**
```
Error: Invalid tool definition
{"message": "function.parameters must be a valid JSON Schema"}
```

**Cause:** Malformed function calling schema.

**Solution:**
```typescript
// Correct tool schema
const tool = {
  type: 'function',
  function: {
    name: 'get_weather', // lowercase, underscores
    description: 'Get weather for a location',
    parameters: {
      type: 'object',
      properties: {
        location: {
          type: 'string', // Valid JSON Schema types
          description: 'City name',
        },
      },
      required: ['location'], // Array of required property names
    },
  },
};
```

## Quick Diagnostic Commands

```bash
set -euo pipefail
# Check API connectivity
curl -I https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}"

# List available models
curl https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" | jq '.data[].id'

# Check local configuration
env | grep MISTRAL

# Test basic chat
curl https://api.mistral.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  -d '{
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Escalation Path
1. Collect evidence with `mistral-debug-bundle`
2. Check Mistral status page: https://status.mistral.ai/
3. Contact support via Discord or email

## Resources
- [Mistral AI Status Page](https://status.mistral.ai/)
- [Mistral AI Discord](https://discord.gg/mistralai)
- [Mistral AI API Reference](https://docs.mistral.ai/api/)

## Next Steps
For comprehensive debugging, see `mistral-debug-bundle`.

## Examples

**Basic usage**: Apply mistral common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize mistral common errors for production environments with multiple constraints and team-specific requirements.