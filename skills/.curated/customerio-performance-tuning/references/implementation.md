# Customer.io Performance Tuning - Implementation Details

## Configuration

### Optimized Client Setup

```typescript
import { TrackClient, RegionUS } from '@customerio/track';

const cio = new TrackClient(
  process.env.CIO_SITE_ID!,
  process.env.CIO_API_KEY!,
  {
    region: RegionUS,
    timeout: 5000,
  }
);
```

## Advanced Patterns

### Batch Event Processing

```typescript
class CustomerIOBatcher {
  private buffer: Array<{ userId: string; event: string; data: any }> = [];
  private flushInterval: NodeJS.Timeout;

  constructor(
    private cio: TrackClient,
    private maxSize = 100,
    private flushMs = 5000
  ) {
    this.flushInterval = setInterval(() => this.flush(), flushMs);
  }

  add(userId: string, event: string, data: any) {
    this.buffer.push({ userId, event, data });
    if (this.buffer.length >= this.maxSize) this.flush();
  }

  async flush() {
    if (this.buffer.length === 0) return;
    const batch = this.buffer.splice(0, this.maxSize);
    const results = await Promise.allSettled(
      batch.map((item) => this.cio.track(item.userId, { name: item.event, data: item.data }))
    );
    const failed = results.filter((r) => r.status === 'rejected');
    if (failed.length > 0) console.warn(`${failed.length}/${batch.length} events failed`);
  }

  destroy() {
    clearInterval(this.flushInterval);
    return this.flush();
  }
}
```

### Connection Pooling for High Throughput

```typescript
import { Agent } from 'https';

const keepAliveAgent = new Agent({
  keepAlive: true,
  maxSockets: 50,
  maxFreeSockets: 10,
  timeout: 10000,
});

// Pass to the underlying HTTP client
const cio = new TrackClient(siteId, apiKey, {
  region: RegionUS,
  agent: keepAliveAgent,
});
```

### Attribute Update Debouncing

```typescript
class AttributeDebouncer {
  private pending = new Map<string, { attrs: Record<string, any>; timer: NodeJS.Timeout }>();

  constructor(private cio: TrackClient, private debounceMs = 2000) {}

  update(userId: string, attrs: Record<string, any>) {
    const existing = this.pending.get(userId);
    if (existing) {
      clearTimeout(existing.timer);
      Object.assign(existing.attrs, attrs);
    }

    const entry = existing ?? { attrs: { ...attrs }, timer: null as any };
    entry.timer = setTimeout(() => {
      this.cio.identify(userId, entry.attrs);
      this.pending.delete(userId);
    }, this.debounceMs);

    this.pending.set(userId, entry);
  }
}
```

### Response Time Monitoring

```typescript
async function timedTrack(userId: string, event: string, data: any) {
  const start = performance.now();
  try {
    await cio.track(userId, { name: event, data });
    const duration = performance.now() - start;
    metrics.histogram('cio.track.duration_ms', duration, { event });
    if (duration > 1000) console.warn(`Slow CIO track: ${event} took ${duration}ms`);
  } catch (err) {
    metrics.increment('cio.track.errors', { event });
    throw err;
  }
}
```

## Troubleshooting

### Identifying Bottlenecks

```bash
# Check Customer.io API response times
for i in $(seq 1 5); do
  curl -o /dev/null -s -w "Response: %{http_code} Time: %{time_total}s\n" \
    -X POST -H "Authorization: Bearer $CIO_API_KEY" \
    -d '{"email":"test@test.com"}' \
    https://track.customer.io/api/v2/entity
done

# Monitor connection reuse
ss -tn | grep "track.customer.io" | wc -l
```

### Diagnosing High Latency

Check these in order: DNS resolution, TLS handshake, server response time:

```bash
curl -w "DNS: %{time_namelookup}s\nTLS: %{time_appconnect}s\nResponse: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
  -o /dev/null -s https://track.customer.io/api/v2/entity
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
