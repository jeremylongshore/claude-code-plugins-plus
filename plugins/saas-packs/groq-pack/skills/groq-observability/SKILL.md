---
name: groq-observability
description: 'Set up observability for Groq integrations: latency histograms, token
  throughput,

  rate limit gauges, cost tracking, and Prometheus alerts.

  Use when instrumenting Groq API calls, building a metrics dashboard, or wiring
  latency/cost/rate-limit alerts.

  Trigger with phrases like "groq monitoring", "groq metrics",

  "groq observability", "monitor groq", "groq alerts", "groq dashboard".

  '
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- monitoring
- observability
- dashboard
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Observability

## Overview

Monitor Groq LPU inference for latency, token throughput, rate limit utilization, and cost. Groq's defining advantage is speed (280-560 tok/s), so latency degradation is the highest-priority signal. The API returns rich timing metadata (`queue_time`, `prompt_time`, `completion_time`) and rate limit headers on every response.

## Prerequisites

- A Groq account with an API key exported as the `GROQ_API_KEY` environment variable — the `groq-sdk` client reads it automatically (`new Groq()`).
- Node.js with `groq-sdk` and `prom-client` installed (`npm install groq-sdk prom-client`).
- A Prometheus scrape target and (optionally) Grafana for the dashboard panels.

## Key Metrics to Track

| Metric | Type | Source | Why |
|--------|------|--------|-----|
| TTFT (time to first token) | Histogram | Client-side timing | Groq's main value prop |
| Tokens/second | Gauge | `usage.completion_time` | Throughput degradation |
| Total latency | Histogram | Client-side timing | End-to-end performance |
| Rate limit remaining | Gauge | `x-ratelimit-remaining-*` headers | Prevent 429s |
| Token usage | Counter | `usage.total_tokens` | Cost attribution |
| Error rate by code | Counter | Error handler | Availability |
| Estimated cost | Counter | Tokens * model price | Budget tracking |

## Instructions

Apply these six steps in order. Steps 1-2 are the core instrumentation loop —
wrap the client, then feed a Prometheus instrument set from each call. Steps 3-6
add rate-limit tracking, alerting, structured logs, and dashboards on top. The
lean client skeleton is below; the full code for every step lives in
[references/implementation.md](references/implementation.md).

1. **Instrumented client** — wrap `groq.chat.completions.create` so latency, tokens, queue time, and estimated cost are captured on the same path as the request (`trackedCompletion`).
2. **Prometheus metrics** — register a histogram (latency), counters (tokens, cost, errors), and gauges (throughput, rate-limit remaining), then feed them from `emitMetrics`.
3. **Rate limit header tracking** — parse `x-ratelimit-remaining-*` off every response into a gauge so you alert before a 429, not after.
4. **Prometheus alert rules** — ship latency/rate-limit/throughput/error/cost alerts tuned to Groq's sub-200ms, 280+ tok/s baseline.
5. **Structured request logging** — emit one JSON line per request for log aggregation, preserving per-request detail metrics roll up.
6. **Dashboard panels** — TTFT distribution, tokens/sec, rate-limit utilization, request volume, error rate, cost, and queue time.

```typescript
import Groq from "groq-sdk";

const groq = new Groq(); // reads GROQ_API_KEY

async function trackedCompletion(model: string, messages: any[]) {
  const start = performance.now();
  const result = await groq.chat.completions.create({ model, messages });
  const latencyMs = performance.now() - start;
  const usage = result.usage!;
  const metrics = {
    model,
    latencyMs: Math.round(latencyMs),
    tokensPerSec: Math.round(usage.completion_tokens / ((usage as any).completion_time || latencyMs / 1000)),
    totalTokens: usage.total_tokens,
  };
  emitMetrics(metrics); // -> Prometheus (Step 2)
  return { result, metrics };
}
```

See [references/implementation.md](references/implementation.md) for the complete
`GroqMetrics` shape, pricing table, Prometheus instruments, rate-limit tracking,
alert rules, structured logging, and dashboard panel list.

## Output

Applying the workflow produces:

- A **`trackedCompletion` wrapper** that returns `{ result, metrics }`, where `metrics` is a `GroqMetrics` object (latency, TTFT, tokens/sec, token counts, queue time, estimated cost).
- A **Prometheus metric set** — `groq_latency_ms` (histogram), `groq_tokens_total` / `groq_cost_usd` / `groq_errors_total` (counters), and `groq_tokens_per_second` / `groq_ratelimit_remaining` (gauges).
- **Five alert rules** (`GroqLatencyHigh`, `GroqRateLimitCritical`, `GroqThroughputDrop`, `GroqErrorRateHigh`, `GroqCostSpike`).
- A **structured JSON log line** per request and a **7-panel dashboard** spec.

## Examples

Instrument a single completion and emit a structured log line:

```typescript
const { result, metrics } = await trackedCompletion(
  "llama-3.3-70b-versatile",
  [{ role: "user", content: "Summarize this incident report in two sentences." }]
);
logGroqRequest(metrics, result.id);
// metrics.tokensPerSec -> 310, metrics.estimatedCostUsd -> 0.000404
```

For a 429-guard using rate-limit headers and a dashboard health-reading table,
see [references/examples.md](references/examples.md).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 with high retry-after | RPM or TPM exhausted | Implement request queuing |
| Latency spike > 2s | Model overloaded or large prompt | Reduce prompt size or switch to lighter model |
| 503 Service Unavailable | Groq capacity issue | Enable fallback to alternative provider |
| Tokens/sec drop | Streaming disabled or large prompts | Enable streaming for better perceived performance |

## Resources

- [references/implementation.md](references/implementation.md) — full code for all six observability steps.
- [references/examples.md](references/examples.md) — worked instrumentation, 429-guard, and dashboard-reading examples.
- [Groq API Reference (usage fields)](https://console.groq.com/docs/api-reference)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [prom-client on npm](https://www.npmjs.com/package/prom-client)
- For incident response procedures, see the `groq-incident-runbook` skill.
