# Step 4: Rate Limit Monitor

Deep-dive reference for the `figma-rate-limits` skill — extracted from the 'Step 4: Rate Limit Monitor' step of the workflow.

```typescript
class FigmaRateLimitMonitor {
  private requestLog: number[] = [];
  private windowMs = 60_000; // 1 minute window

  recordRequest() {
    this.requestLog.push(Date.now());
    // Trim old entries
    const cutoff = Date.now() - this.windowMs;
    this.requestLog = this.requestLog.filter(t => t > cutoff);
  }

  getRequestsInWindow(): number {
    const cutoff = Date.now() - this.windowMs;
    return this.requestLog.filter(t => t > cutoff).length;
  }

  shouldThrottle(safetyMargin = 0.8): boolean {
    // If we've used 80% of a conservative estimate, slow down
    const estimatedLimit = 30; // Conservative estimate
    return this.getRequestsInWindow() > estimatedLimit * safetyMargin;
  }
}

const monitor = new FigmaRateLimitMonitor();

// Wrap every request
async function monitoredFigmaFetch(path: string, token: string) {
  if (monitor.shouldThrottle()) {
    console.warn('Approaching rate limit, adding delay');
    await new Promise(r => setTimeout(r, 2000));
  }
  monitor.recordRequest();
  return figmaFetchWithRetry(path, token);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
