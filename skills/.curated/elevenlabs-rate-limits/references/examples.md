# ElevenLabs Rate Limits — Worked Examples

End-to-end usage examples that build on the four building blocks in
[implementation.md](implementation.md).

## Example 1: Batch generation on a Pro plan (queue only)

Generate 20 clips while never exceeding the Pro plan's 10 concurrent requests. The
queue paces submission; each clip resolves as soon as a slot frees up.

```typescript
import { createRequestQueue } from "./elevenlabs/rate-limiter";

const queue = createRequestQueue("pro"); // 10 concurrent

const texts = loadScripts();            // e.g. 20 lines of narration
const voiceId = "21m00Tcm4TlvDq8ikWAM";

const clips = await Promise.all(
  texts.map(text =>
    queue.add(() =>
      client.textToSpeech.convert(voiceId, { text, model_id: "eleven_flash_v2_5" })
    )
  )
);
// clips.length === 20, but at most 10 requests were ever in flight
```

## Example 2: Full resilient client (queue + backoff + quota guard)

The recommended production path. `generateSpeech` guards quota, queues to respect
concurrency, and backs off on `system_busy` — all in one call.

```typescript
import { createResilientClient } from "./elevenlabs/resilient-client";

const el = createResilientClient("pro");

// Quota is checked before the request; concurrency + backoff are automatic.
const audio = await el.generateSpeech(
  "21m00Tcm4TlvDq8ikWAM",
  "Welcome to the show.",
  "eleven_multilingual_v2"
);

console.log(el.getQueueStats()); // { pending: 0, size: 0 }

const quota = await el.checkQuota();
if (quota.warning) {
  console.warn(`Approaching quota: ${quota.pctUsed}% used`);
}
```

## Example 3: Distinguishing the two 429 variants at the call site

If you handle retries yourself instead of using `withBackoff`, branch on the
`detail.status` field to pick the right strategy.

```typescript
try {
  await client.textToSpeech.convert(voiceId, { text, model_id: "eleven_v3" });
} catch (error: any) {
  const type = error.body?.detail?.status;
  if (type === "too_many_concurrent_requests") {
    // Requeue — do NOT back off; a slot will open shortly.
    await queue.add(() => retry());
  } else if (type === "system_busy") {
    // Server overload — exponential backoff with jitter.
    await withBackoff(() => retry());
  } else {
    throw error; // auth/validation errors are non-retryable
  }
}
```
