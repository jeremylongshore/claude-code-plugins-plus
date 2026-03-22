---
name: abridge-rate-limits
description: |
  Implement Abridge rate limiting, backoff, and session throttling patterns.
  Use when handling 429 errors, managing concurrent encounter sessions,
  or optimizing API throughput for high-volume clinical deployments.
  Trigger: "abridge rate limit", "abridge 429", "abridge throttling",
  "abridge concurrent sessions".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, rate-limiting]
compatible-with: claude-code
---

# Abridge Rate Limits

## Overview

Abridge enforces rate limits per organization to ensure platform stability across thousands of concurrent clinical encounters. Limits vary by contract tier and are enforced at the org_id level.

## Rate Limit Tiers

| Tier | Concurrent Sessions | API Calls/min | Note Generations/min | WebSocket Connections |
|------|---------------------|---------------|---------------------|-----------------------|
| Pilot | 10 | 60 | 10 | 10 |
| Standard | 100 | 600 | 50 | 100 |
| Enterprise | 1,000+ | 6,000 | 500 | 1,000 |

## Response Headers

```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1711234567
Retry-After: 30
```

## Instructions

### Step 1: Rate Limit Aware Client

```typescript
// src/abridge/rate-limiter.ts
interface RateLimitState {
  remaining: number;
  limit: number;
  resetAt: Date;
  retryAfter?: number;
}

class AbridgeRateLimiter {
  private state: RateLimitState = {
    remaining: Infinity,
    limit: Infinity,
    resetAt: new Date(),
  };
  private queue: Array<{ resolve: () => void; reject: (err: Error) => void }> = [];
  private processing = false;

  updateFromHeaders(headers: Record<string, string>): void {
    if (headers['x-ratelimit-remaining']) {
      this.state.remaining = parseInt(headers['x-ratelimit-remaining']);
    }
    if (headers['x-ratelimit-limit']) {
      this.state.limit = parseInt(headers['x-ratelimit-limit']);
    }
    if (headers['x-ratelimit-reset']) {
      this.state.resetAt = new Date(parseInt(headers['x-ratelimit-reset']) * 1000);
    }
    if (headers['retry-after']) {
      this.state.retryAfter = parseInt(headers['retry-after']);
    }
  }

  async waitForSlot(): Promise<void> {
    if (this.state.remaining > 0) {
      this.state.remaining--;
      return;
    }

    // Wait until rate limit resets
    const waitMs = Math.max(0, this.state.resetAt.getTime() - Date.now());
    console.log(`Rate limited — waiting ${waitMs}ms for reset`);
    await new Promise(r => setTimeout(r, waitMs));
    this.state.remaining = this.state.limit;
  }

  get utilizationPercent(): number {
    return ((this.state.limit - this.state.remaining) / this.state.limit) * 100;
  }
}

export { AbridgeRateLimiter };
```

### Step 2: Concurrent Session Manager

```typescript
// src/abridge/session-pool.ts
import Bottleneck from 'bottleneck';

// Manage concurrent encounter sessions within org limits
const sessionLimiter = new Bottleneck({
  maxConcurrent: 50,          // Stay under tier limit
  minTime: 100,               // 100ms between session creates
  reservoir: 50,              // Burst capacity
  reservoirRefreshInterval: 60000,  // Refill every minute
  reservoirRefreshAmount: 50,
});

sessionLimiter.on('depleted', () => {
  console.warn('Session pool depleted — queuing new sessions');
});

async function createSessionThrottled(
  api: any,
  patientId: string,
  providerId: string,
  specialty: string,
): Promise<any> {
  return sessionLimiter.schedule(() =>
    api.post('/encounters/sessions', {
      patient_id: patientId,
      provider_id: providerId,
      specialty,
      encounter_type: 'outpatient',
    })
  );
}

export { createSessionThrottled, sessionLimiter };
```

### Step 3: 429 Error Handler with Retry-After

```typescript
// src/abridge/retry-429.ts
import axios, { AxiosError } from 'axios';

async function handleRateLimitedRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 5,
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (err) {
      const axiosErr = err as AxiosError;
      if (axiosErr.response?.status !== 429 || attempt === maxRetries) {
        throw err;
      }

      const retryAfter = axiosErr.response.headers['retry-after'];
      const waitMs = retryAfter
        ? parseInt(retryAfter as string) * 1000
        : Math.min(1000 * Math.pow(2, attempt), 60000);

      console.log(`429 rate limited — retry ${attempt}/${maxRetries} in ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Usage Monitoring

```typescript
// src/abridge/usage-monitor.ts
interface UsageSnapshot {
  timestamp: string;
  activeSessions: number;
  apiCallsThisMinute: number;
  noteGenerationsThisMinute: number;
  utilizationPercent: number;
}

class UsageMonitor {
  private snapshots: UsageSnapshot[] = [];
  private apiCallCount = 0;
  private noteGenCount = 0;

  recordApiCall(): void { this.apiCallCount++; }
  recordNoteGeneration(): void { this.noteGenCount++; }

  takeSnapshot(activeSessions: number): UsageSnapshot {
    const snapshot: UsageSnapshot = {
      timestamp: new Date().toISOString(),
      activeSessions,
      apiCallsThisMinute: this.apiCallCount,
      noteGenerationsThisMinute: this.noteGenCount,
      utilizationPercent: (activeSessions / 100) * 100, // Adjust per tier
    };
    this.snapshots.push(snapshot);
    this.apiCallCount = 0;
    this.noteGenCount = 0;
    return snapshot;
  }

  getAlerts(): string[] {
    const latest = this.snapshots.at(-1);
    if (!latest) return [];
    const alerts: string[] = [];
    if (latest.utilizationPercent > 80) alerts.push('Session utilization > 80%');
    if (latest.apiCallsThisMinute > 500) alerts.push('API calls approaching limit');
    return alerts;
  }
}
```

## Output

- Rate-limit-aware API client with header parsing
- Concurrent session pool with Bottleneck throttling
- Automatic 429 retry with Retry-After header support
- Usage monitoring with utilization alerts

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded org rate limit | Use Retry-After header; implement backoff |
| `503 Service Unavailable` | Platform-wide throttling | Back off exponentially; check status page |
| Session create rejected | Concurrent session limit | Queue creates with Bottleneck |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [Bottleneck Rate Limiter](https://www.npmjs.com/package/bottleneck)

## Next Steps

For security configuration, see `abridge-security-basics`.
