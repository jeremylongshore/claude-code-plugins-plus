# Step 2: Prometheus Metrics

Deep-dive reference for the `figma-observability` skill — extracted from the 'Step 2: Prometheus Metrics' step of the workflow.

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const figmaRequests = new Counter({
  name: 'figma_api_requests_total',
  help: 'Total Figma API requests',
  labelNames: ['endpoint', 'status'],
  registers: [registry],
});

const figmaLatency = new Histogram({
  name: 'figma_api_request_duration_seconds',
  help: 'Figma API request duration in seconds',
  labelNames: ['endpoint'],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

const figmaRateLimitRemaining = new Gauge({
  name: 'figma_rate_limit_remaining',
  help: 'Remaining Figma API rate limit',
  registers: [registry],
});

const figmaCacheHits = new Counter({
  name: 'figma_cache_hits_total',
  help: 'Figma cache hits vs misses',
  labelNames: ['result'], // 'hit' or 'miss'
  registers: [registry],
});

// Expose /metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
