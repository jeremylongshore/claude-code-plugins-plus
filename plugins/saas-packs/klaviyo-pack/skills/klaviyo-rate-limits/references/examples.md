# Klaviyo Rate Limits — Worked Examples

These examples compose the building blocks defined in `SKILL.md` (Step 1) and
`references/implementation.md` (Steps 2–4). Nothing here introduces new SDK
behavior — it only wires the existing helpers together for common tasks.

## Example 1: A single rate-safe call

Wrap one Klaviyo SDK call so it honors `Retry-After` and backs off on 5xx:

```typescript
import { withRateLimitRetry } from './klaviyo/rate-limiter';

const profile = await withRateLimitRetry(() =>
  profilesApi.getProfile('01H...')
);
```

If the account is over its burst window, the call sleeps for exactly the number
of seconds Klaviyo returns in `Retry-After`, then retries — up to `maxRetries`
(default 5) before rethrowing.

## Example 2: High-volume writes through the queue

For fan-out work, route every call through the queue so requests leave the
process at a safe 60 req/s instead of a burst that trips the 75 req/s wall:

```typescript
import { queuedKlaviyoCall } from './klaviyo/queue';

await Promise.all(
  events.map(e =>
    queuedKlaviyoCall(() => eventsApi.createEvent({ data: e }))
  )
);
```

The queue paces the requests; `withRateLimitRetry` (called inside
`queuedKlaviyoCall`) still absorbs any 429 that slips through.

## Example 3: Import 100k profiles without a 429 storm

```typescript
import { bulkProfileSync } from './klaviyo/bulk';

const { success, failed } = await bulkProfileSync(
  profiles,      // Array of { email, firstName?, properties? }
  50,            // batchSize
  1000           // delayMs between batches
);

console.log(`[Klaviyo] Imported ${success}, failed ${failed}`);
```

## Example 4: Throttle proactively using live headers

When you already hold a response, feed its headers to the monitor and pause
before the next call if the remaining budget is low:

```typescript
import { rateLimitMonitor } from './klaviyo/monitor';

const res = await profilesApi.getProfilesRaw({});
rateLimitMonitor.updateFromHeaders(res.raw.headers);

if (rateLimitMonitor.shouldThrottle()) {
  await new Promise(r => setTimeout(r, rateLimitMonitor.getWaitMs()));
}
```
