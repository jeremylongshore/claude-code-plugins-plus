---
name: deepgram-rate-limits
description: |
  Implement Deepgram rate limiting and backoff strategies.
  Use when handling API quotas, implementing request throttling,
  or dealing with 429 rate limit errors.
  Trigger: "deepgram rate limit", "deepgram throttling", "429 error deepgram",
  "deepgram quota", "deepgram backoff", "deepgram concurrency".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, api, rate-limiting]

---
# Deepgram Rate Limits

## Overview
Implement rate limiting, exponential backoff, and circuit breaker patterns for Deepgram API. Deepgram limits by **concurrent connections** (not requests per second). Understanding this model is key to building reliable integrations.

## Deepgram Rate Limit Model

Deepgram uses **concurrency-based** limits, not traditional requests-per-minute:

| Plan | Concurrent Requests (STT) | Concurrent Connections (Live) | Concurrent Requests (TTS) |
|------|---------------------------|-------------------------------|---------------------------|
| Pay As You Go | 100 | 100 | 100 |
| Growth | 200 | 200 | 200 |
| Enterprise | Custom | Custom | Custom |

When you exceed your concurrency limit, Deepgram returns `429 Too Many Requests`.

**Key insight:** You can send unlimited total requests — just not more than your concurrency limit *simultaneously*.

## Instructions

### Step 1: Concurrency-Aware Queue

```typescript
import pLimit from 'p-limit';
import { createClient } from '@deepgram/sdk';

class DeepgramRateLimiter {
  private limit: ReturnType<typeof pLimit>;
  private client: ReturnType<typeof createClient>;
  private stats = { total: 0, active: 0, queued: 0, errors: 0 };

  constructor(apiKey: string, maxConcurrent = 50) {
    // Stay well under plan limit (e.g., 50 of 100 allowed)
    this.limit = pLimit(maxConcurrent);
    this.client = createClient(apiKey);
  }

  async transcribe(source: { url: string }, options: Record<string, any>) {
    this.stats.queued++;
    return this.limit(async () => {
      this.stats.queued--;
      this.stats.active++;
      this.stats.total++;
      try {
        const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
          source, options
        );
        if (error) {
          this.stats.errors++;
          throw error;
        }
        return result;
      } catch (err) {
        this.stats.errors++;
        throw err;
      } finally {
        this.stats.active--;
      }
    });
  }

  getStats() { return { ...this.stats }; }
}

// Usage:
const limiter = new DeepgramRateLimiter(process.env.DEEPGRAM_API_KEY!, 50);
const urls = ['audio1.wav', 'audio2.wav', /* ...hundreds more */];
const results = await Promise.allSettled(
  urls.map(url => limiter.transcribe({ url }, { model: 'nova-3', smart_format: true }))
);
```

### Step 2: Exponential Backoff with Jitter

```typescript
class RetryableDeepgramClient {
  private client: ReturnType<typeof createClient>;

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeWithRetry(
    source: any,
    options: any,
    config = { maxRetries: 5, baseDelay: 1000, maxDelay: 60000 }
  ) {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
          source, options
        );
        if (!error) return result;

        // Non-retryable errors (4xx except 429, 408)
        const status = (error as any).status;
        if (status >= 400 && status < 500 && status !== 429 && status !== 408) {
          throw new Error(`Non-retryable error ${status}: ${error.message}`);
        }
        lastError = error;
      } catch (err: any) {
        if (err.message.startsWith('Non-retryable')) throw err;
        lastError = err;
      }

      if (attempt < config.maxRetries) {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s + random jitter
        const delay = Math.min(
          config.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
          config.maxDelay
        );
        console.log(`Retry ${attempt + 1}/${config.maxRetries} in ${Math.round(delay)}ms`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
    throw lastError ?? new Error('Max retries exceeded');
  }
}
```

### Step 3: Circuit Breaker

```typescript
enum CircuitState { CLOSED, OPEN, HALF_OPEN }

class DeepgramCircuitBreaker {
  private state = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime = 0;
  private successCount = 0;

  constructor(
    private failureThreshold = 5,
    private resetTimeout = 30000,     // 30 seconds
    private halfOpenMaxRequests = 3,
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime >= this.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      } else {
        throw new Error(`Circuit OPEN — retry in ${
          Math.ceil((this.resetTimeout - (Date.now() - this.lastFailureTime)) / 1000)
        }s`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  private onSuccess() {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.halfOpenMaxRequests) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    if (this.failureCount >= this.failureThreshold) {
      this.state = CircuitState.OPEN;
      console.error(`Circuit OPEN after ${this.failureCount} failures`);
    }
  }

  getState() { return CircuitState[this.state]; }
}
```

### Step 4: Combined Rate Limiter + Circuit Breaker

```typescript
class ResilientDeepgramClient {
  private limiter: DeepgramRateLimiter;
  private breaker: DeepgramCircuitBreaker;
  private retryClient: RetryableDeepgramClient;

  constructor(apiKey: string, maxConcurrent = 50) {
    this.limiter = new DeepgramRateLimiter(apiKey, maxConcurrent);
    this.breaker = new DeepgramCircuitBreaker();
    this.retryClient = new RetryableDeepgramClient(apiKey);
  }

  async transcribe(audioUrl: string, options: Record<string, any> = {}) {
    return this.breaker.execute(() =>
      this.retryClient.transcribeWithRetry(
        { url: audioUrl },
        { model: 'nova-3', smart_format: true, ...options }
      )
    );
  }
}

// Production usage
const client = new ResilientDeepgramClient(process.env.DEEPGRAM_API_KEY!, 50);
const result = await client.transcribe('https://example.com/audio.wav');
```

### Step 5: Usage Monitoring

```typescript
// Query Deepgram's usage API to track consumption
async function checkUsage(client: ReturnType<typeof createClient>, projectId: string) {
  const { result } = await client.manage.getUsage(projectId, {
    start: new Date(Date.now() - 86400000).toISOString(), // Last 24 hours
    end: new Date().toISOString(),
  });

  const totalMinutes = (result as any).results?.reduce(
    (sum: number, r: any) => sum + (r.hours * 60 + r.minutes), 0
  ) ?? 0;

  console.log(`Last 24h usage: ${totalMinutes.toFixed(1)} minutes`);
  return totalMinutes;
}
```

## Output
- Concurrency-aware request queue with `p-limit`
- Exponential backoff with jitter for 429/5xx errors
- Circuit breaker (CLOSED -> OPEN -> HALF_OPEN)
- Combined resilient client pattern
- Usage monitoring via Deepgram API

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| 429 Too Many Requests | Concurrency limit exceeded | Lower `maxConcurrent`, implement backoff |
| Circuit breaker OPEN | 5+ consecutive failures | Wait for reset, check status.deepgram.com |
| Queue growing unbounded | Sustained high load | Increase plan limits or scale horizontally |
| Usage API returns empty | Wrong project ID | Verify project ID from `getProjects()` |

## Resources
- [Concurrency Rate Limits](https://developers.deepgram.com/docs/working-with-concurrency-rate-limits)
- [API Rate Limits](https://developers.deepgram.com/reference/api-rate-limits)
- [Backoff Strategies](https://deepgram.com/learn/api-back-off-strategies)
- [Usage API](https://developers.deepgram.com/reference/get-usage)
