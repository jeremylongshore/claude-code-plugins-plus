# Step 2: Track API Usage

Deep-dive reference for the `figma-cost-tuning` skill — extracted from the 'Step 2: Track API Usage' step of the workflow.

```typescript
// Instrument all Figma API calls to track volume
class FigmaUsageTracker {
  private calls: Array<{ endpoint: string; timestamp: number; cached: boolean }> = [];

  record(endpoint: string, cached: boolean) {
    this.calls.push({ endpoint, timestamp: Date.now(), cached });
  }

  getReport(windowMs = 24 * 60 * 60 * 1000) {
    const cutoff = Date.now() - windowMs;
    const recent = this.calls.filter(c => c.timestamp > cutoff);

    // Group by endpoint
    const byEndpoint = new Map<string, { total: number; cached: number }>();
    for (const call of recent) {
      const key = call.endpoint.replace(/[a-zA-Z0-9]{20,}/, ':key');
      const entry = byEndpoint.get(key) || { total: 0, cached: 0 };
      entry.total++;
      if (call.cached) entry.cached++;
      byEndpoint.set(key, entry);
    }

    return {
      totalCalls: recent.length,
      cachedCalls: recent.filter(c => c.cached).length,
      cacheHitRate: recent.length > 0
        ? (recent.filter(c => c.cached).length / recent.length * 100).toFixed(1) + '%'
        : '0%',
      byEndpoint: Object.fromEntries(byEndpoint),
    };
  }
}

const tracker = new FigmaUsageTracker();
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
