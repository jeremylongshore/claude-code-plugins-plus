---
name: fireflies-rate-limits
description: |
  Implement Fireflies.ai rate limiting, backoff, and request queuing.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Fireflies.ai.
  Trigger with phrases like "fireflies rate limit", "fireflies throttling",
  "fireflies 429", "fireflies retry", "fireflies backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api]

---
# Fireflies.ai Rate Limits

## Overview
Handle Fireflies.ai GraphQL API rate limits with exponential backoff and request queuing. Fireflies enforces per-plan limits and per-operation limits.

## Rate Limit Reference

### Per-Plan Limits
| Plan | Limit | Scope |
|------|-------|-------|
| Free | 50 requests/day | Per API key |
| Pro | 50 requests/day | Per API key |
| Business | 60 requests/min | Per API key |
| Enterprise | 60 requests/min | Per API key |

### Per-Operation Limits
| Operation | Limit | Error Code |
|-----------|-------|------------|
| `addToLiveMeeting` | 3 per 20 minutes | `too_many_requests` |
| `shareMeeting` | 10 per hour (up to 50 emails each) | `too_many_requests` |
| `deleteTranscript` | 10 per minute | `too_many_requests` |
| `uploadAudio` | Varies by plan | `too_many_requests` |

## Instructions

### Step 1: Detect Rate Limits in Responses
```typescript
interface FirefliesError {
  message: string;
  code: string;
  extensions?: { status: number };
}

function isRateLimited(response: any): boolean {
  return response.errors?.some(
    (e: FirefliesError) =>
      e.code === "too_many_requests" ||
      e.extensions?.status === 429
  );
}
```

### Step 2: Exponential Backoff with Jitter
```typescript
async function firefliesQueryWithRetry<T>(
  query: string,
  variables?: Record<string, any>,
  maxRetries = 5
): Promise<T> {
  const FIREFLIES_API = "https://api.fireflies.ai/graphql";

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(FIREFLIES_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
      },
      body: JSON.stringify({ query, variables }),
    });

    const json = await res.json();

    if (!isRateLimited(json)) {
      if (json.errors) throw new Error(json.errors[0].message);
      return json.data;
    }

    if (attempt === maxRetries) {
      throw new Error(`Rate limited after ${maxRetries} retries`);
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter
    const baseDelay = 1000 * Math.pow(2, attempt);
    const jitter = Math.random() * 500;
    const delay = Math.min(baseDelay + jitter, 32000);

    console.log(`Rate limited. Retry ${attempt + 1}/${maxRetries} in ${delay.toFixed(0)}ms`);
    await new Promise(r => setTimeout(r, delay));
  }

  throw new Error("Unreachable");
}
```

### Step 3: Request Queue for Batch Operations
```typescript
import PQueue from "p-queue";

// Business plan: 60 req/min = 1 req/sec safe rate
const firefliesQueue = new PQueue({
  concurrency: 1,
  interval: 1100,
  intervalCap: 1,
});

async function queuedQuery<T>(query: string, variables?: Record<string, any>): Promise<T> {
  return firefliesQueue.add(() => firefliesQueryWithRetry<T>(query, variables));
}

// Batch fetch transcripts without hitting rate limits
async function batchFetchTranscripts(ids: string[]) {
  const results = [];
  for (const id of ids) {
    const data = await queuedQuery(`
      query GetTranscript($id: String!) {
        transcript(id: $id) {
          id title date duration
          summary { overview action_items }
        }
      }
    `, { id });
    results.push(data);
  }
  return results;
}
```

### Step 4: Free/Pro Plan Daily Budget Tracker
```typescript
class DailyBudgetTracker {
  private count = 0;
  private resetDate = new Date().toDateString();
  private readonly dailyLimit: number;

  constructor(plan: "free" | "pro" | "business") {
    this.dailyLimit = plan === "business" ? Infinity : 50;
  }

  canRequest(): boolean {
    this.resetIfNewDay();
    return this.count < this.dailyLimit;
  }

  record(): void {
    this.resetIfNewDay();
    this.count++;
  }

  remaining(): number {
    this.resetIfNewDay();
    return Math.max(0, this.dailyLimit - this.count);
  }

  private resetIfNewDay(): void {
    const today = new Date().toDateString();
    if (today !== this.resetDate) {
      this.count = 0;
      this.resetDate = today;
    }
  }
}

const budget = new DailyBudgetTracker("pro");
if (!budget.canRequest()) {
  console.log("Daily API limit reached. Try again tomorrow.");
}
```

## Error Handling
| Scenario | Detection | Action |
|----------|-----------|--------|
| 429 response | `code: "too_many_requests"` | Exponential backoff |
| Daily limit hit (Free/Pro) | Track request count | Wait until next day |
| `addToLiveMeeting` throttle | 3 per 20 min | Queue with 7-min spacing |
| Burst of webhook events | Many transcripts at once | Queue transcript fetches |

## Output
- Rate-limit-aware GraphQL client with automatic retry
- Request queue preventing burst-induced throttling
- Daily budget tracker for Free/Pro plans

## Resources
- [Fireflies API Rate Limits](https://docs.fireflies.ai/fundamentals/concepts)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `fireflies-security-basics`.
