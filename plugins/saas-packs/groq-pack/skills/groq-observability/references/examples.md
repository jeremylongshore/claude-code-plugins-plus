# Groq Observability — Worked Examples

These examples compose the helpers defined in
[implementation.md](implementation.md) into end-to-end flows. The parent
[SKILL.md](../SKILL.md) summarizes the workflow; use this file to see the pieces
wired together.

## Example 1: Instrument a completion and log the result

Wrap a normal chat call with `trackedCompletion`, then emit a structured log
line. Metrics flow to Prometheus via `emitMetrics` automatically inside the
wrapper.

```typescript
const { result, metrics } = await trackedCompletion(
  "llama-3.3-70b-versatile",
  [{ role: "user", content: "Summarize this incident report in two sentences." }],
  { maxTokens: 256 }
);

// Emit a structured JSON log line for aggregation
logGroqRequest(metrics, result.id);

// metrics -> {
//   model: "llama-3.3-70b-versatile",
//   latencyMs: 180, ttftMs: 40, tokensPerSec: 310,
//   promptTokens: 620, completionTokens: 48, totalTokens: 668,
//   queueTimeMs: 8, estimatedCostUsd: 0.000404
// }
```

The emitted `groq_latency_ms`, `groq_tokens_total`, `groq_tokens_per_second`,
and `groq_cost_usd` series feed straight into the Step 4 alert rules — no extra
wiring needed.

## Example 2: Guard against a 429 using rate-limit headers

Read the `x-ratelimit-remaining-*` headers off a response and back off before
the quota is exhausted, instead of catching the 429 after the fact.

```typescript
const response = await groq.chat.completions.with_raw_response.create({
  model: "llama-3.1-8b-instant",
  messages: [{ role: "user", content: "classify: positive or negative?" }],
});

const remaining = trackRateLimitHeaders(response.headers);
// remaining -> { requests: 4, tokens: 12000 }

if (remaining.requests < 5) {
  // The GroqRateLimitCritical alert (Step 4) is already firing at this point.
  await new Promise((r) => setTimeout(r, 1000)); // simple backoff
}
```

## Example 3: Reading the dashboard

With the panels from Step 6 in place, a healthy Groq deployment reads:

| Panel | Healthy | Investigate |
|-------|---------|-------------|
| TTFT Distribution | P95 < 500ms | P95 > 1s → `GroqLatencyHigh` |
| Tokens/Second | 280–560 | < 100 → `GroqThroughputDrop` |
| Rate Limit Utilization | < 90% | > 90% → approaching `GroqRateLimitCritical` |
| Error Rate | < 1% | > 5% → `GroqErrorRateHigh` |
| Queue Time | < 50ms | sustained > 200ms → Groq-side congestion |

When any panel crosses into the "investigate" column, hand off to the
`groq-incident-runbook` skill for response procedures.
