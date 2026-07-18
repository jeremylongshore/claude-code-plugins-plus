# Notion Load & Scale — Worked Examples

Supporting utilities referenced from `SKILL.md`. Use these to plan capacity
before a bulk run and to measure real per-call latency against your workspace.

## Capacity Calculator

Estimate whether a planned read/write mix fits within your token budget before
launching a bulk job. Accounts for cache hit rate (reads served from cache do
not consume the API budget) and for horizontal scaling across multiple
integration tokens (each token adds 3 req/s).

```typescript
function calculateCapacity(config: {
  readsPerMinute: number;
  writesPerMinute: number;
  cacheHitRate: number;
  integrationTokens: number;
}) {
  const effectiveReads = config.readsPerMinute * (1 - config.cacheHitRate);
  const totalPerMinute = effectiveReads + config.writesPerMinute;
  const reqPerSecond = totalPerMinute / 60;
  const capacity = config.integrationTokens * 3;

  console.log('=== Capacity Plan ===');
  console.log(`Effective req/s: ${reqPerSecond.toFixed(1)} / ${capacity} capacity`);
  console.log(`Headroom: ${((1 - reqPerSecond / capacity) * 100).toFixed(0)}%`);
  console.log(reqPerSecond > capacity ? 'OVER CAPACITY' : 'Within limits');
}
```

## Quick Throughput Benchmark

Measure baseline per-call latency against the live API. The `sleep 0.34` keeps
the loop under 3 req/s so the benchmark itself never trips the rate limit.

```bash
# Time 10 sequential API calls to measure baseline latency
time for i in $(seq 1 10); do
  curl -s -o /dev/null -w "%{time_total}\n" \
    https://api.notion.com/v1/users/me \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28"
  sleep 0.34
done
```
