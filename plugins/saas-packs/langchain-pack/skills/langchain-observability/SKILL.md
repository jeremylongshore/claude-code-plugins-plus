---
name: langchain-observability
description: |
  Set up comprehensive observability for LangChain applications
  with LangSmith tracing, OpenTelemetry, Prometheus metrics, and alerts.
  Trigger: "langchain monitoring", "langchain metrics", "langchain observability",
  "langchain tracing", "LangSmith", "langchain alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, monitoring, observability, dashboard]

---
# LangChain Observability

## Overview

Production observability for LangChain: LangSmith tracing (zero-code), custom Prometheus metrics, OpenTelemetry integration, structured logging, and Grafana dashboards.

## Tier 1: LangSmith Tracing (Zero-Code Setup)

LangSmith automatically traces all LangChain calls when env vars are set.

```bash
# Add to .env — that's it. No code changes needed.
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=my-app-production

# Optional: background callbacks for lower latency (non-serverless)
LANGCHAIN_CALLBACKS_BACKGROUND=true
```

Every chain, LLM call, tool invocation, and retriever query is automatically traced with:
- Input/output payloads
- Token usage and cost
- Latency per step
- Error details with stack traces
- Parent-child run relationships

### Query Traces Programmatically

```typescript
import { Client } from "langsmith";

const client = new Client();

// Get recent failed runs
const failedRuns = client.listRuns({
  projectName: "my-app-production",
  error: true,
  limit: 10,
});

for await (const run of failedRuns) {
  console.log(`${run.name}: ${run.error} (${run.totalTokens} tokens)`);
}
```

## Tier 2: Custom Metrics Callback

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

interface Metrics {
  totalRequests: number;
  totalErrors: number;
  totalTokens: number;
  latencies: number[];
}

class MetricsCallback extends BaseCallbackHandler {
  name = "MetricsCallback";
  metrics: Metrics = { totalRequests: 0, totalErrors: 0, totalTokens: 0, latencies: [] };
  private startTimes = new Map<string, number>();

  handleLLMStart(_llm: any, _prompts: string[], runId: string) {
    this.metrics.totalRequests++;
    this.startTimes.set(runId, Date.now());
  }

  handleLLMEnd(output: any, runId: string) {
    const start = this.startTimes.get(runId);
    if (start) {
      this.metrics.latencies.push(Date.now() - start);
      this.startTimes.delete(runId);
    }
    const usage = output.llmOutput?.tokenUsage;
    if (usage) {
      this.metrics.totalTokens += (usage.totalTokens ?? 0);
    }
  }

  handleLLMError(_error: Error, runId: string) {
    this.metrics.totalErrors++;
    this.startTimes.delete(runId);
  }

  getReport() {
    const latencies = this.metrics.latencies;
    const sorted = [...latencies].sort((a, b) => a - b);
    return {
      requests: this.metrics.totalRequests,
      errors: this.metrics.totalErrors,
      errorRate: this.metrics.totalRequests > 0
        ? (this.metrics.totalErrors / this.metrics.totalRequests * 100).toFixed(1) + "%"
        : "0%",
      totalTokens: this.metrics.totalTokens,
      p50Latency: sorted[Math.floor(sorted.length * 0.5)] ?? 0,
      p95Latency: sorted[Math.floor(sorted.length * 0.95)] ?? 0,
      p99Latency: sorted[Math.floor(sorted.length * 0.99)] ?? 0,
    };
  }
}

// Usage
const metrics = new MetricsCallback();
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  callbacks: [metrics],
});

// After some operations:
console.table(metrics.getReport());
```

## Tier 3: Prometheus Exporter (Python)

```python
from prometheus_client import Counter, Histogram, start_http_server
from langchain_core.callbacks import BaseCallbackHandler

# Define metrics
llm_requests = Counter("langchain_llm_requests_total", "LLM requests", ["model", "status"])
llm_latency = Histogram("langchain_llm_latency_seconds", "LLM latency", ["model"])
llm_tokens = Counter("langchain_llm_tokens_total", "Tokens used", ["model", "type"])

class PrometheusCallback(BaseCallbackHandler):
    def __init__(self):
        self._start_times = {}

    def on_llm_start(self, serialized, prompts, run_id, **kwargs):
        self._start_times[str(run_id)] = time.time()

    def on_llm_end(self, response, run_id, **kwargs):
        model = "unknown"
        elapsed = time.time() - self._start_times.pop(str(run_id), time.time())

        llm_requests.labels(model=model, status="success").inc()
        llm_latency.labels(model=model).observe(elapsed)

        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            llm_tokens.labels(model=model, type="input").inc(usage.get("prompt_tokens", 0))
            llm_tokens.labels(model=model, type="output").inc(usage.get("completion_tokens", 0))

    def on_llm_error(self, error, run_id, **kwargs):
        self._start_times.pop(str(run_id), None)
        llm_requests.labels(model="unknown", status="error").inc()

# Start metrics server on :9090
start_http_server(9090)
```

## Tier 4: Grafana Dashboard Queries

```
# Request rate
rate(langchain_llm_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(langchain_llm_latency_seconds_bucket[5m]))

# Error rate percentage
sum(rate(langchain_llm_requests_total{status="error"}[5m]))
/ sum(rate(langchain_llm_requests_total[5m])) * 100

# Token usage per hour
increase(langchain_llm_tokens_total[1h])
```

## Alerting Rules

```yaml
# prometheus/rules/langchain.yml
groups:
  - name: langchain
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(langchain_llm_requests_total{status="error"}[5m]))
          / sum(rate(langchain_llm_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "LangChain error rate above 5%"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(langchain_llm_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "LangChain P95 latency above 5 seconds"

      - alert: TokenBudgetExceeded
        expr: increase(langchain_llm_tokens_total[1d]) > 1000000
        labels: { severity: warning }
        annotations:
          summary: "Daily token usage exceeded 1M"
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Missing traces in LangSmith | Env vars not set | Verify `LANGSMITH_TRACING=true` |
| Callback not firing | Not passed to model | Add to `callbacks: [handler]` in constructor |
| Metrics missing in Prometheus | Server not started | Call `start_http_server(9090)` |
| Alert storms | Thresholds too sensitive | Tune `for` duration and thresholds |

## Resources

- [LangSmith Docs](https://docs.smith.langchain.com/)
- [LangSmith Tracing Guide](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_langchain)
- [OpenTelemetry + LangSmith](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_opentelemetry)
- [Prometheus Python Client](https://prometheus.io/docs/instrumenting/clientlibs/)

## Next Steps

Use `langchain-incident-runbook` for incident response procedures.
