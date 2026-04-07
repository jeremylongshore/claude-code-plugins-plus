---
name: hex-rate-limits
description: |
  Implement Hex rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Hex.
  Trigger with phrases like "hex rate limit", "hex throttling",
  "hex 429", "hex retry", "hex backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Rate Limits

## Overview

Hex's API enforces tight limits on project run triggers (20 per minute, 60 per hour) while leaving read operations like status checks and project listing largely unthrottled. Data teams scheduling batch analytics runs or triggering parameterized notebooks from CI/CD pipelines must carefully manage the hourly cap, since a single pipeline triggering 15 projects can consume a quarter of the hourly budget. Polling run status is free, but triggering runs is the bottleneck that shapes integration architecture.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| RunProject (trigger) | 20 req | 1 minute | Per API token |
| RunProject (trigger) | 60 req | 1 hour | Per API token |
| GetRunStatus | No hard limit | - | Per API token |
| ListProjects | No hard limit | - | Per API token |
| CancelRun | No hard limit | - | Per API token |

## Rate Limiter Implementation

```typescript
class HexRateLimiter {
  private minuteTokens: number = 20;
  private hourlyTokens: number = 60;
  private lastMinuteRefill: number = Date.now();
  private lastHourlyRefill: number = Date.now();
  private queue: Array<{ resolve: () => void }> = [];

  async acquire(): Promise<void> {
    this.refill();
    if (this.minuteTokens >= 1 && this.hourlyTokens >= 1) {
      this.minuteTokens -= 1;
      this.hourlyTokens -= 1;
      return;
    }
    return new Promise(resolve => this.queue.push({ resolve }));
  }

  private refill() {
    const now = Date.now();
    this.minuteTokens = Math.min(20, this.minuteTokens + ((now - this.lastMinuteRefill) / 60_000) * 20);
    this.lastMinuteRefill = now;
    this.hourlyTokens = Math.min(60, this.hourlyTokens + ((now - this.lastHourlyRefill) / 3_600_000) * 60);
    this.lastHourlyRefill = now;
    while (this.minuteTokens >= 1 && this.hourlyTokens >= 1 && this.queue.length) {
      this.minuteTokens -= 1;
      this.hourlyTokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const runLimiter = new HexRateLimiter();
```

## Retry Strategy

```typescript
async function hexRunWithRetry(
  projectId: string, params: Record<string, any>, maxRetries = 3
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await runLimiter.acquire();
    const res = await fetch(`${HEX_BASE}/api/v1/run/${projectId}`, {
      method: "POST", headers,
      body: JSON.stringify({ inputParams: params }),
    });
    if (res.ok) return res.json();
    if (res.status === 429) {
      const delay = 30_000 * Math.pow(2, attempt) + Math.random() * 5000;
      await new Promise(r => setTimeout(r, delay));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 3000));
      continue;
    }
    throw new Error(`Hex API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchRunProjects(projects: Array<{ id: string; params: any }>, batchSize = 5) {
  const results: any[] = [];
  for (let i = 0; i < projects.length; i += batchSize) {
    const batch = projects.slice(i, i + batchSize);
    const runs = await Promise.all(
      batch.map(p => hexRunWithRetry(p.id, p.params))
    );
    // Poll for completion
    for (const run of runs) {
      let status = run;
      while (status.status === "RUNNING") {
        await new Promise(r => setTimeout(r, 5000));
        const res = await fetch(`${HEX_BASE}/api/v1/run/${run.runId}/status`, { headers });
        status = await res.json();
      }
      results.push(status);
    }
    if (i + batchSize < projects.length) await new Promise(r => setTimeout(r, 15_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on RunProject | Exceeded 20/min or 60/hour trigger limit | Queue runs, space 5s apart minimum |
| Run stuck in RUNNING | Long-running query or compute timeout | Poll up to 30 min, then CancelRun |
| 401 on scheduled run | API token rotated | Refresh token in CI secrets before batch |
| Empty run output | Project has no published outputs | Verify project has published cells |
| 409 concurrent run | Same project triggered twice | Check run status before re-triggering |

## Resources

- [Hex API Documentation](https://learn.hex.tech/docs/api/api-overview)

## Next Steps

See `hex-performance-tuning`.
