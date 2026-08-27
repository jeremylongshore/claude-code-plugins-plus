# Groq Observability — Full Implementation

This reference holds the complete, copy-pasteable code for each observability
step. The parent [SKILL.md](../SKILL.md) summarizes the workflow and shows the
instrumented-client skeleton; drill in here for the full implementation of each
step.

## Step 1: Instrumented Groq Client

Wrap every completion so timing, token, queue, and cost data are captured on the
same code path as the request itself.

```typescript
import Groq from "groq-sdk";

const groq = new Groq();

interface GroqMetrics {
  model: string;
  latencyMs: number;
  ttftMs: number;
  tokensPerSec: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  queueTimeMs: number;
  estimatedCostUsd: number;
}

const PRICE_PER_1M: Record<string, { input: number; output: number }> = {
  "llama-3.1-8b-instant": { input: 0.05, output: 0.08 },
  "llama-3.3-70b-versatile": { input: 0.59, output: 0.79 },
  "llama-3.3-70b-specdec": { input: 0.59, output: 0.99 },
  "meta-llama/llama-4-scout-17b-16e-instruct": { input: 0.11, output: 0.34 },
};

async function trackedCompletion(
  model: string,
  messages: any[],
  options?: { maxTokens?: number; temperature?: number }
): Promise<{ result: any; metrics: GroqMetrics }> {
  const start = performance.now();

  const result = await groq.chat.completions.create({
    model,
    messages,
    max_tokens: options?.maxTokens ?? 1024,
    temperature: options?.temperature ?? 0.7,
  });

  const latencyMs = performance.now() - start;
  const usage = result.usage!;
  const pricing = PRICE_PER_1M[model] || { input: 0.10, output: 0.10 };

  const metrics: GroqMetrics = {
    model,
    latencyMs: Math.round(latencyMs),
    ttftMs: Math.round(((usage as any).prompt_time ?? 0) * 1000),
    tokensPerSec: Math.round(
      usage.completion_tokens / ((usage as any).completion_time || latencyMs / 1000)
    ),
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    totalTokens: usage.total_tokens,
    queueTimeMs: Math.round(((usage as any).queue_time ?? 0) * 1000),
    estimatedCostUsd:
      (usage.prompt_tokens / 1_000_000) * pricing.input +
      (usage.completion_tokens / 1_000_000) * pricing.output,
  };

  emitMetrics(metrics);
  return { result, metrics };
}
```

## Step 2: Prometheus Metrics

Register the histogram/counter/gauge instruments once, then feed them from
`emitMetrics` on every tracked completion.

```typescript
import { Histogram, Counter, Gauge } from "prom-client";

const groqLatency = new Histogram({
  name: "groq_latency_ms",
  help: "Groq API latency in milliseconds",
  labelNames: ["model"],
  buckets: [50, 100, 200, 500, 1000, 2000, 5000],
});

const groqTokens = new Counter({
  name: "groq_tokens_total",
  help: "Total tokens processed",
  labelNames: ["model", "direction"],
});

const groqThroughput = new Gauge({
  name: "groq_tokens_per_second",
  help: "Current tokens per second",
  labelNames: ["model"],
});

const groqRateLimitRemaining = new Gauge({
  name: "groq_ratelimit_remaining",
  help: "Remaining rate limit quota",
  labelNames: ["type"],
});

const groqCost = new Counter({
  name: "groq_cost_usd",
  help: "Estimated cost in USD",
  labelNames: ["model"],
});

const groqErrors = new Counter({
  name: "groq_errors_total",
  help: "API errors by status code",
  labelNames: ["model", "status_code"],
});

function emitMetrics(m: GroqMetrics) {
  groqLatency.labels(m.model).observe(m.latencyMs);
  groqTokens.labels(m.model, "input").inc(m.promptTokens);
  groqTokens.labels(m.model, "output").inc(m.completionTokens);
  groqThroughput.labels(m.model).set(m.tokensPerSec);
  groqCost.labels(m.model).inc(m.estimatedCostUsd);
}
```

## Step 3: Rate Limit Header Tracking

Every Groq response carries `x-ratelimit-remaining-*` headers. Feed them into
the gauge so you can alert before a 429 rather than after.

```typescript
// Parse rate limit headers from any Groq response
function trackRateLimitHeaders(headers: Record<string, string>) {
  const remaining = {
    requests: parseInt(headers["x-ratelimit-remaining-requests"] || "0"),
    tokens: parseInt(headers["x-ratelimit-remaining-tokens"] || "0"),
  };

  groqRateLimitRemaining.labels("requests").set(remaining.requests);
  groqRateLimitRemaining.labels("tokens").set(remaining.tokens);

  return remaining;
}
```

## Step 4: Prometheus Alert Rules

Ship these alert rules alongside the metrics. Thresholds are tuned to Groq's
normal profile (sub-200ms latency, 280+ tok/s).

```yaml
# prometheus/groq-alerts.yml
groups:
  - name: groq
    rules:
      - alert: GroqLatencyHigh
        expr: histogram_quantile(0.95, rate(groq_latency_ms_bucket[5m])) > 1000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Groq P95 latency > 1s (normally < 200ms)"

      - alert: GroqRateLimitCritical
        expr: groq_ratelimit_remaining{type="requests"} < 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Groq rate limit nearly exhausted (< 5 requests remaining)"

      - alert: GroqThroughputDrop
        expr: groq_tokens_per_second < 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Groq throughput dropped below 100 tok/s (expected 280+)"

      - alert: GroqErrorRateHigh
        expr: rate(groq_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Groq API error rate elevated (> 5% of requests)"

      - alert: GroqCostSpike
        expr: increase(groq_cost_usd[1h]) > 10
        labels:
          severity: warning
        annotations:
          summary: "Groq spend exceeded $10 in the past hour"
```

## Step 5: Structured Request Logging

Emit one structured JSON line per request for log aggregation (Loki, Datadog,
CloudWatch). Keeps the per-request detail that metrics aggregate away.

```typescript
// Structured JSON log for each Groq request
function logGroqRequest(metrics: GroqMetrics, requestId?: string) {
  const logEntry = {
    ts: new Date().toISOString(),
    service: "groq",
    model: metrics.model,
    latency_ms: metrics.latencyMs,
    ttft_ms: metrics.ttftMs,
    tokens_per_sec: metrics.tokensPerSec,
    prompt_tokens: metrics.promptTokens,
    completion_tokens: metrics.completionTokens,
    queue_time_ms: metrics.queueTimeMs,
    cost_usd: metrics.estimatedCostUsd.toFixed(6),
    request_id: requestId,
  };

  // Output as structured JSON for log aggregation
  console.log(JSON.stringify(logEntry));
}
```

## Step 6: Dashboard Panels

Key Grafana/dashboard panels for Groq monitoring:

1. **TTFT Distribution** (histogram) -- Groq's main value; alert if > 500ms
2. **Tokens/Second by Model** (time series) -- should be 280-560 range
3. **Rate Limit Utilization** (gauge, 0-100%) -- alert at 90%
4. **Request Volume** (counter rate) -- by model
5. **Error Rate** (counter rate) -- by status code (429, 5xx)
6. **Cumulative Cost** (counter) -- by model, daily/weekly/monthly
7. **Queue Time** (histogram) -- Groq-specific, should be < 50ms
