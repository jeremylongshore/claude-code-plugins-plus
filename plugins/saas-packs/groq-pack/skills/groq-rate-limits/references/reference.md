# Groq Rate Limits — Reference Tables & Worked Examples

## Rate Limit Structure

Groq rate limits vary by plan and model. Limits are applied simultaneously --
you must stay under both RPM and TPM.

| Constraint | Description |
|-----------|-------------|
| RPM | Requests per minute |
| RPD | Requests per day |
| TPM | Tokens per minute |
| TPD | Tokens per day |

Free tier limits are significantly lower than paid tier. Check your current
limits at [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

## Rate Limit Response Headers

When Groq responds (even on success), it includes these headers:

| Header | Description |
|--------|-------------|
| `x-ratelimit-limit-requests` | Max requests in current window |
| `x-ratelimit-limit-tokens` | Max tokens in current window |
| `x-ratelimit-remaining-requests` | Requests remaining before limit |
| `x-ratelimit-remaining-tokens` | Tokens remaining before limit |
| `x-ratelimit-reset-requests` | Time until request limit resets |
| `x-ratelimit-reset-tokens` | Time until token limit resets |
| `retry-after` | Seconds to wait (only on 429 responses) |

## Worked Example — Composed Client

Wire the queue, monitor, and retry wrapper together so every call is gated,
tracked, and retried automatically.

```typescript
import Groq from "groq-sdk";
import PQueue from "p-queue";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const queue = createGroqQueue(30);          // Step 3
const monitor = new RateLimitMonitor();     // Step 4

async function safeCompletion(messages: any[], model: string) {
  await monitor.waitIfNeeded();             // pause before hitting the limit
  const chosen = await smartModelSelect(messages, model, monitor); // Step 5
  return queue.add(() =>
    withRateLimitRetry(async () => {        // Step 2
      const res = await groq.chat.completions.create({ model: chosen, messages });
      monitor.update((res as any)._request_id ? {} : {}); // update from response headers
      return res;
    })
  );
}

// Fan out 100 requests without tripping the free-tier 30 RPM limit
const jobs = Array.from({ length: 100 }, (_, i) =>
  safeCompletion([{ role: "user", content: `Summarize item ${i}` }],
    "llama-3.3-70b-versatile")
);
const results = await Promise.all(jobs);
console.log(`Completed ${results.length} requests`, monitor.getStatus());
```

## Worked Example — Parsing a 429

```typescript
try {
  await groq.chat.completions.create({ model, messages });
} catch (err) {
  if (err instanceof Groq.APIError && err.status === 429) {
    const retryAfter = parseInt(err.headers?.["retry-after"] || "0");
    console.log(`Rate limited. retry-after says wait ${retryAfter}s.`);
    // -> feed retryAfter into withRateLimitRetry (Step 2)
  }
}
```
