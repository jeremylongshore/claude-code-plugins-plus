# Klaviyo Performance Tuning — Worked Examples

These scenarios combine the building blocks from `implementation.md` to solve
common real-world performance problems. Each one composes the caching, pagination,
batching, and concurrency primitives defined in the main workflow.

## Example 1: Fast, cached profile lookup by email

Combines sparse fieldsets (Step 1) with response caching (Step 2) so a repeated
lookup during a request burst hits memory instead of the API.

```typescript
import { cachedKlaviyoCall } from './cache';

async function getProfileFast(email: string) {
  return cachedKlaviyoCall(
    `profile:${email}`,
    () => profilesApi.getProfiles({
      filter: `equals(email,"${email}")`,
      fieldsProfile: ['email', 'first_name', 'created'],  // sparse payload
    }),
    5 * 60 * 1000  // 5 minute TTL
  );
}
```

## Example 2: Export every profile in a large list

Combines cursor pagination (Step 3) with a bounded `maxPages` guard so an export
of a multi-hundred-thousand-member list terminates predictably.

```typescript
import { fetchAllPages } from './pagination';

async function exportList(listId: string) {
  const allProfiles = await fetchAllPages(
    (cursor) => listsApi.getListProfiles({ id: listId, pageCursor: cursor }),
    { maxPages: 500 }  // hard ceiling — process in chunks beyond this
  );
  console.log(`Exported ${allProfiles.length} profiles`);
  return allProfiles;
}
```

## Example 3: Bulk-update 10,000 profiles under the rate limit

Combines the `PQueue` concurrency controller (Step 5) with progress logging so a
large write job stays under Klaviyo's 75 req/s burst / 700 req/min ceiling.

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 10, interval: 1000, intervalCap: 50 });

async function bulkUpdate(updates: Array<{ email: string; data: any }>) {
  await Promise.allSettled(
    updates.map(u => queue.add(() =>
      profilesApi.createOrUpdateProfile({
        data: { type: 'profile' as any, attributes: { email: u.email, ...u.data } },
      })
    ))
  );
}
```

## Example 4: Measure where the time goes

Wrap any of the above in `measuredCall` (Step 6) and read a p95 summary to find
the slow operation before you optimize it.

```typescript
import { measuredCall, getPerfSummary } from './perf-monitor';

await measuredCall('getProfileFast', () => getProfileFast('a@example.com'), true);
await measuredCall('exportList', () => exportList(listId));

console.table(getPerfSummary());
// { getProfileFast: { avg: 2, p95: 5, count: 40 },
//   exportList:     { avg: 210, p95: 480, count: 12 } }
```
