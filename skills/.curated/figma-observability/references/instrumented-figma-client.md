# Step 1: Instrumented Figma Client

Deep-dive reference for the `figma-observability` skill — extracted from the 'Step 1: Instrumented Figma Client' step of the workflow.

```typescript
// Wrap every Figma API call with metrics and logging
class InstrumentedFigmaClient {
  private metrics = {
    requests: 0,
    errors: 0,
    rateLimits: 0,
    totalLatencyMs: 0,
  };

  async request<T>(path: string, token: string): Promise<T> {
    const start = performance.now();
    const endpoint = path.replace(/[a-zA-Z0-9]{15,}/, ':key'); // normalize

    try {
      const res = await fetch(`https://api.figma.com${path}`, {
        headers: { 'X-Figma-Token': token },
      });

      const latencyMs = performance.now() - start;
      this.metrics.requests++;
      this.metrics.totalLatencyMs += latencyMs;

      // Log every request with structured data
      console.log(JSON.stringify({
        service: 'figma',
        endpoint,
        status: res.status,
        latencyMs: Math.round(latencyMs),
        rateLimit: {
          remaining: res.headers.get('X-RateLimit-Remaining'),
          type: res.headers.get('X-Figma-Rate-Limit-Type'),
        },
      }));

      if (res.status === 429) {
        this.metrics.rateLimits++;
        const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
        throw new FigmaRateLimitError(retryAfter);
      }

      if (!res.ok) {
        this.metrics.errors++;
        throw new FigmaApiError(res.status, await res.text());
      }

      return res.json();
    } catch (error) {
      if (!(error instanceof FigmaApiError)) {
        this.metrics.errors++;
        console.error(JSON.stringify({
          service: 'figma',
          endpoint,
          error: error instanceof Error ? error.message : 'Unknown',
          latencyMs: Math.round(performance.now() - start),
        }));
      }
      throw error;
    }
  }

  getMetrics() {
    return {
      ...this.metrics,
      avgLatencyMs: this.metrics.requests > 0
        ? Math.round(this.metrics.totalLatencyMs / this.metrics.requests)
        : 0,
      errorRate: this.metrics.requests > 0
        ? (this.metrics.errors / this.metrics.requests * 100).toFixed(1) + '%'
        : '0%',
    };
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
