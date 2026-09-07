# Apify Rate Limits — Worked Examples

End-to-end examples that combine the building blocks from
[implementation.md](implementation.md) into complete scenarios.

## Example 1: Bulk dataset push without 429s

Collapse a per-item loop into batched, chunked pushes so 50,000 rows cost a handful
of API calls instead of 50,000.

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const dsId = 'my-dataset-id';

function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

// 50,000 records → ~50 API calls at 1000/chunk (vs 50,000 unbatched)
for (const chunk of chunkArray(records, 1000)) {
  await client.dataset(dsId).pushItems(chunk);
}
```

## Example 2: Fan-out reads through a queue

Read 500 Actors' metadata in parallel while staying under 50 req/sec.

```typescript
import PQueue from 'p-queue';

const apiQueue = new PQueue({ concurrency: 10, interval: 1000, intervalCap: 50 });
const rateLimitedCall = <T>(fn: () => Promise<T>) => apiQueue.add(fn) as Promise<T>;

const metadata = await Promise.all(
  actorIds.map(id => rateLimitedCall(() => client.actor(id).get()))
);
```

## Example 3: Launch 100 runs safely

Stagger 100 Actor starts with a 200 ms delay so the runs endpoint never 429s, then
wait for every run to finish.

```typescript
import { sleep } from 'crawlee';

async function staggeredRuns(actorId, inputs, delayMs = 200) {
  const runs = [];
  for (const input of inputs) {
    runs.push(await client.actor(actorId).start(input));
    await sleep(delayMs);
  }
  return Promise.all(runs.map(run => client.run(run.id).waitForFinish()));
}

const finished = await staggeredRuns('my-actor', hundredInputs);
```

## Example 4: Pause on header-driven exhaustion

Use the monitor to sleep exactly until the limit resets instead of guessing.

```typescript
const monitor = new ApifyRateLimitMonitor(10);

for (const batch of batches) {
  if (monitor.shouldPause()) {
    await new Promise(r => setTimeout(r, monitor.getWaitMs()));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  monitor.updateFromHeaders(Object.fromEntries(res.headers.entries()));
}
```
