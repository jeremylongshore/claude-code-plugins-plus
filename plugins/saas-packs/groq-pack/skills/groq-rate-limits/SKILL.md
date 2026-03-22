---
name: groq-rate-limits
description: |
  Implement Groq rate limit handling with backoff, queuing, and header parsing.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Groq.
  Trigger with phrases like "groq rate limit", "groq throttling",
  "groq 429", "groq retry", "groq backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api]

---
# Groq Rate Limits

## Overview
Handle Groq rate limits using the `retry-after` header, exponential backoff, and request queuing. Groq enforces limits at the organization level with both RPM (requests/minute) and TPM (tokens/minute) constraints -- hitting either one triggers a `429`.

## Rate Limit Structure
Groq rate limits vary by plan and model. Limits are applied simultaneously -- you must stay under both RPM and TPM.

| Constraint | Description |
|-----------|-------------|
| RPM | Requests per minute |
| RPD | Requests per day |
| TPM | Tokens per minute |
| TPD | Tokens per day |

Free tier limits are significantly lower than paid tier. Check your current limits at [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

## Rate Limit Response Headers
When Groq responds (even on success), it includes these headers:

| Header | Description |
|--------|-------------|
| `x-ratelimit-limit-requests` | Max requests in current window |
| `x-ratelimit-limit-tokens` | Max tokens in current window |
| `x-ratelimit-remaining-requests` | Requests remaining before limit |
| `x-ratelimit-remaining-tokens` | Tokens remaining before limit |
| `x-ratelimit-reset-requests` | Time until request limit resets |
| `x-ratelimit-reset-tokens` | Time until token limit resets |
| `retry-after` | Seconds to wait (only on 429 responses) |

## Instructions

### Step 1: Parse Rate Limit Headers
```typescript
import Groq from "groq-sdk";

interface RateLimitInfo {
  limitRequests: number;
  limitTokens: number;
  remainingRequests: number;
  remainingTokens: number;
  resetRequestsMs: number;
  resetTokensMs: number;
}

function parseRateLimitHeaders(headers: Record<string, string>): RateLimitInfo {
  return {
    limitRequests: parseInt(headers["x-ratelimit-limit-requests"] || "0"),
    limitTokens: parseInt(headers["x-ratelimit-limit-tokens"] || "0"),
    remainingRequests: parseInt(headers["x-ratelimit-remaining-requests"] || "0"),
    remainingTokens: parseInt(headers["x-ratelimit-remaining-tokens"] || "0"),
    resetRequestsMs: parseResetTime(headers["x-ratelimit-reset-requests"]),
    resetTokensMs: parseResetTime(headers["x-ratelimit-reset-tokens"]),
  };
}

function parseResetTime(value?: string): number {
  if (!value) return 0;
  // Groq returns reset times like "1.2s" or "120ms"
  if (value.endsWith("ms")) return parseFloat(value);
  if (value.endsWith("s")) return parseFloat(value) * 1000;
  return parseFloat(value) * 1000;
}
```

### Step 2: Exponential Backoff with Retry-After
```typescript
async function withRateLimitRetry<T>(
  operation: () => Promise<T>,
  options = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60_000 }
): Promise<T> {
  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === options.maxRetries) throw err;

      if (err instanceof Groq.APIError && err.status === 429) {
        // Prefer retry-after header from Groq
        const retryAfterSec = parseInt(err.headers?.["retry-after"] || "0");
        let delayMs: number;

        if (retryAfterSec > 0) {
          delayMs = retryAfterSec * 1000;
        } else {
          // Exponential backoff with jitter
          const exponential = options.baseDelayMs * Math.pow(2, attempt);
          const jitter = Math.random() * 500;
          delayMs = Math.min(exponential + jitter, options.maxDelayMs);
        }

        console.warn(`Rate limited (attempt ${attempt + 1}/${options.maxRetries}). Waiting ${(delayMs / 1000).toFixed(1)}s...`);
        await new Promise((r) => setTimeout(r, delayMs));
        continue;
      }

      // Non-rate-limit errors: only retry 5xx
      if (err instanceof Groq.APIError && err.status >= 500) {
        const delayMs = options.baseDelayMs * Math.pow(2, attempt);
        await new Promise((r) => setTimeout(r, delayMs));
        continue;
      }

      throw err; // 4xx (except 429) are not retryable
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Request Queue with Concurrency Control
```typescript
import PQueue from "p-queue";

// Queue that respects Groq RPM limits
function createGroqQueue(requestsPerMinute: number) {
  return new PQueue({
    intervalCap: requestsPerMinute,
    interval: 60_000,  // 1 minute window
    concurrency: 5,    // Max parallel requests
  });
}

const queue = createGroqQueue(30); // Free tier: 30 RPM

async function queuedCompletion(messages: any[], model: string) {
  return queue.add(() =>
    withRateLimitRetry(() =>
      groq.chat.completions.create({ model, messages })
    )
  );
}
```

### Step 4: Proactive Rate Limit Monitor
```typescript
class RateLimitMonitor {
  private remaining = { requests: Infinity, tokens: Infinity };
  private resets = { requests: 0, tokens: 0 };

  update(headers: Record<string, string>): void {
    const info = parseRateLimitHeaders(headers);
    this.remaining.requests = info.remainingRequests;
    this.remaining.tokens = info.remainingTokens;
    this.resets.requests = Date.now() + info.resetRequestsMs;
    this.resets.tokens = Date.now() + info.resetTokensMs;
  }

  shouldThrottle(): boolean {
    return this.remaining.requests < 3 || this.remaining.tokens < 500;
  }

  async waitIfNeeded(): Promise<void> {
    if (!this.shouldThrottle()) return;

    const waitMs = Math.max(
      this.resets.requests - Date.now(),
      this.resets.tokens - Date.now(),
      0
    );

    if (waitMs > 0) {
      console.log(`Throttling: waiting ${(waitMs / 1000).toFixed(1)}s for rate limit reset`);
      await new Promise((r) => setTimeout(r, waitMs));
    }
  }

  getStatus(): string {
    return `Requests: ${this.remaining.requests} remaining | Tokens: ${this.remaining.tokens} remaining`;
  }
}
```

### Step 5: Model-Aware Rate Limit Strategy
```typescript
// Different models have different limits -- route accordingly
async function smartModelSelect(
  messages: any[],
  preferredModel: string,
  monitor: RateLimitMonitor
): Promise<string> {
  // If rate limited on preferred model, try a different one
  if (monitor.shouldThrottle()) {
    const fallbacks: Record<string, string> = {
      "llama-3.3-70b-versatile": "llama-3.1-8b-instant",
      "llama-3.1-8b-instant": "llama-3.3-70b-versatile", // Different limit pool
    };
    const fallback = fallbacks[preferredModel];
    if (fallback) {
      console.log(`Switching from ${preferredModel} to ${fallback} (rate limit)`);
      return fallback;
    }
  }
  return preferredModel;
}
```

## Error Handling
| Scenario | Symptom | Solution |
|----------|---------|----------|
| Burst of requests | Many 429s in quick succession | Use queue with `p-queue` interval limiting |
| Large prompts burn TPM | 429 on tokens, not requests | Reduce `max_tokens`, compress prompts |
| Free tier too restrictive | Constant 429s | Upgrade to Developer plan at console.groq.com |
| Multiple services sharing key | Cascading 429s | Use separate API keys per service |

## Resources
- [Groq Rate Limits Documentation](https://console.groq.com/docs/rate-limits)
- [Groq Pricing / Plans](https://groq.com/pricing)
- [p-queue on npm](https://www.npmjs.com/package/p-queue)

## Next Steps
For security configuration, see `groq-security-basics`.
