# Groq Rate Limit Handling — Full Implementation

The complete five-step implementation. Each step is standalone; compose them
into a single client wrapper (queue → monitor → retry) for production use.

## Step 1: Parse Rate Limit Headers

Groq returns rate-limit state on every response (even successes). Parse the
headers into a typed structure so the monitor and retry logic can reason about
remaining capacity.

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

## Step 2: Exponential Backoff with Retry-After

Always prefer Groq's `retry-after` header when present; fall back to
exponential backoff with jitter otherwise. Retry only `429` and `5xx`; other
`4xx` errors are not retryable.

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

## Step 3: Request Queue with Concurrency Control

Prevent bursts from ever hitting the limit by gating requests through a
`p-queue` sized to your plan's RPM.

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

## Step 4: Proactive Rate Limit Monitor

Track remaining capacity from response headers and pause *before* you hit the
limit, rather than reacting to `429`s after the fact.

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

## Step 5: Model-Aware Rate Limit Strategy

Different models draw from different limit pools, so falling back to another
model can unblock you without waiting for a reset.

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
