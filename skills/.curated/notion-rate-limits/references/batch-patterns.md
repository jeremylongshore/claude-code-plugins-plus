# Notion Rate Limits — Batch Patterns

## Batch Block Appends

Combine blocks into chunks of 100 instead of one API call per block:

```typescript
function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

const BLOCK_BATCH_SIZE = 100;  // Stay under 1,000 limit
for (const chunk of chunkArray(blocks, BLOCK_BATCH_SIZE)) {
  await throttled(() =>
    notion.blocks.children.append({
      block_id: pageId,
      children: chunk,
    })
  );
}
```

## Batch Processing with Progress Tracking

```typescript
async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  opts = { batchSize: 3, delayMs: 350, label: 'items' }
): Promise<R[]> {
  const results: R[] = [];
  const total = items.length;

  for (let i = 0; i < total; i += opts.batchSize) {
    const batch = items.slice(i, i + opts.batchSize);
    const batchResults = await Promise.all(batch.map(processor));
    results.push(...batchResults);

    const processed = Math.min(i + opts.batchSize, total);
    console.log(`Processed ${processed}/${total} ${opts.label}`);

    if (i + opts.batchSize < total) {
      await new Promise((r) => setTimeout(r, opts.delayMs));
    }
  }
  return results;
}

// Update 200 pages without hitting rate limits
const updates = await processBatch(
  pageIds,
  (id) => notion.pages.update({
    page_id: id,
    properties: { Status: { select: { name: 'Processed' } } },
  }),
  { batchSize: 3, delayMs: 400, label: 'pages' }
);
```

## Python — Batch Processing

```python
import time

def process_batch(items, processor, batch_size=3, delay=0.35, label="items"):
    """Process items in batches with rate limit delays."""
    results = []
    total = len(items)

    for i in range(0, total, batch_size):
        batch = items[i : i + batch_size]
        batch_results = [processor(item) for item in batch]
        results.extend(batch_results)

        processed = min(i + batch_size, total)
        print(f"Processed {processed}/{total} {label}")

        if i + batch_size < total:
            time.sleep(delay)

    return results

# Update 200 pages
updates = process_batch(
    page_ids,
    lambda pid: notion.pages.update(
        page_id=pid,
        properties={"Status": {"select": {"name": "Processed"}}},
    ),
    batch_size=3,
    delay=0.4,
    label="pages",
)
```

## Queue Health Monitoring

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 3, interval: 1000, intervalCap: 3,
  carryoverConcurrencyCount: true,
});

queue.on('active', () => {
  console.log(`Queue: ${queue.size} pending, ${queue.pending} active`);
});
queue.on('idle', () => {
  console.log('Queue drained — all requests complete');
});
queue.on('error', (error) => {
  console.error('Queue error:', error);
});
```
