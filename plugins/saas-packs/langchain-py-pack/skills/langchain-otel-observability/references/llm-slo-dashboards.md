# LLM SLO Dashboards and Burn-Rate Alerts

Five SLIs that matter for an LLM service plus concrete query examples for
Honeycomb, Grafana (Prometheus + Tempo), and Datadog. All five come from
`gen_ai.*` attributes on LangChain spans — you do not need a second pipeline.

## The five SLIs

| SLI | Definition | Why it matters for LLM |
|-----|------------|------------------------|
| **p95 latency (chat)** | 95th percentile end-to-end duration of top-level `LangGraph.invoke` or `Runnable.invoke` | Provider variance is the dominant factor; track per-model so one slow provider does not mask the others |
| **p99 latency (chat)** | 99th percentile of same | Tail latency dominates user perception on chat UIs; agents with many tool calls often live here |
| **error rate** | `errors / total` over a rolling window; `errors` includes `span.status.code = ERROR` plus `gen_ai.response.finish_reason IN ("length", "content_filter")` | Provider 429s, context-length overflow, and safety filters are all "errors" from the user's seat |
| **cost per request** | Sum of `gen_ai.usage.cost_usd` per top-level request | The only SLI that catches silent regression from someone swapping `haiku` → `opus` |
| **time to first token (TTFT)** | Delta from span start to `first_token` span event | For streaming UIs — perceived latency comes from TTFT, not total duration |

## Honeycomb queries

Honeycomb ingests all `gen_ai.*` as first-class columns. Use the Query Builder
or Honeycomb Query Language (triggered from API / Terraform).

### p95 latency per model
```
VISUALIZE: P95(duration_ms)
GROUP BY: gen_ai.request.model
WHERE: name = "LangGraph.invoke"
```

### Error rate
```
VISUALIZE: RATE_MAX(error), COUNT
GROUP BY: gen_ai.request.model, gen_ai.response.finish_reason
WHERE: name = "LangGraph.invoke"
```

### Cost per request (p50, p95)
```
VISUALIZE: P50(gen_ai.usage.cost_usd), P95(gen_ai.usage.cost_usd)
GROUP BY: gen_ai.request.model
WHERE: parent_id = "" (top-level spans only)
```

### TTFT (requires span event instrumentation — see genai-semantic-conventions.md)
```
VISUALIZE: P95(meta.span_events["first_token"].time - start_time)
GROUP BY: gen_ai.request.model
WHERE: gen_ai.request.stream = true
```

## Grafana / Prometheus PromQL

If you're on Grafana + Tempo + Prometheus, emit Prometheus metrics in parallel
to traces via an `opentelemetry-exporter-prometheus` pipeline. Histogram metric
`llm_request_duration_seconds` with labels `model`, `provider`, `status`:

### p95 latency per model (5-minute window)
```promql
histogram_quantile(0.95,
  sum(rate(llm_request_duration_seconds_bucket[5m])) by (le, model)
)
```

### p99 latency per model (5-minute window)
```promql
histogram_quantile(0.99,
  sum(rate(llm_request_duration_seconds_bucket[5m])) by (le, model)
)
```

### Error rate (5-minute rolling)
```promql
sum(rate(llm_requests_total{status="error"}[5m])) by (model)
/
sum(rate(llm_requests_total[5m])) by (model)
```

### Cost per minute (billing-accurate if cost attribute is set)
```promql
sum(rate(llm_cost_usd_total[1m])) by (model, tenant_id) * 60
```

### TTFT p95 (requires separate `llm_ttft_seconds` histogram from callback)
```promql
histogram_quantile(0.95,
  sum(rate(llm_ttft_seconds_bucket[5m])) by (le, model)
)
```

## Datadog LLM Observability queries

Datadog's LLM Observability product pre-computes these. If you are on APM only
(no LLM add-on), query the raw spans:

### p95 latency
```
@operation_name:LangGraph.invoke
| measure @duration p95 by @gen_ai.request.model
```

### Error rate
```
@operation_name:LangGraph.invoke @status:error
/
@operation_name:LangGraph.invoke
```

### Cost (requires custom metric from callback)
```
avg:llm.cost{*} by {gen_ai.request.model}.as_count()
```

## Burn-rate alerts

A burn rate alert fires when you're consuming your error budget faster than the
SLO allows. Standard multi-window multi-burn-rate (MWMBR) pattern from Google
SRE. Example for a 99.5% latency SLO over a 30-day window (error budget = 0.5%,
3.6 hours/month):

### Fast burn (page-worthy) — 14.4× burn, 1hr window
```promql
(
  sum(rate(llm_request_duration_seconds_count{le="5"}[1h]))
  /
  sum(rate(llm_request_duration_seconds_count[1h]))
) < (1 - 14.4 * 0.005)
```
Meaning: if we keep this p95-over-5s rate for a month, we burn 48% of budget.

### Slow burn (ticket-worthy) — 6× burn, 6hr window
```promql
(
  sum(rate(llm_request_duration_seconds_count{le="5"}[6h]))
  /
  sum(rate(llm_request_duration_seconds_count[6h]))
) < (1 - 6 * 0.005)
```

### Cost burn — fires when projected monthly cost exceeds budget
```promql
sum(increase(llm_cost_usd_total[1d])) * 30 > 5000  # $5k/month budget
```

## Dashboard layout (recommended)

Four panels, top to bottom:

1. **Latency SLI** — p50, p95, p99 over time, grouped by model. Include SLO
   threshold as a horizontal line.
2. **Error rate SLI** — stacked area by `finish_reason` (`stop` is success,
   everything else adds to error rate).
3. **Cost panel** — sum of `gen_ai.usage.cost_usd` per hour, stacked by model
   and tenant. Annotate with cost budget.
4. **Volume panel** — request rate by model + TTFT p95 if streaming.

## Sampling caveat for tail-latency SLOs

Head sampling at 10% means 90% of p99 outliers are discarded before they reach
the backend. Your dashboard's p99 becomes noisy and biased toward the median.
Fix with tail sampling at the OTEL Collector:

```yaml
# otel-collector.yaml — tail-sample keeps all error and all slow spans
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors-keep-all
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-keep-all
        type: latency
        latency: {threshold_ms: 5000}
      - name: fast-sample-10pct
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

Tail sampling needs a collector in front of your backend; direct-to-backend
exporters can only head-sample.

## Sources

- Google SRE Workbook: Alerting on SLOs — https://sre.google/workbook/alerting-on-slos/
- Honeycomb query language — https://docs.honeycomb.io/reference/api/query-specification/
- OTEL Collector tail sampling — https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor
