# LLM SLOs — Canonical Set and Burn-Rate Recipes

The four SLOs that map to what LLM users actually feel. HTTP-style SLOs (2xx
ratio, p95 response time) miss TTFT entirely and confuse "provider was up" with
"user got a useful answer."

## The Four SLOs

| SLO | Definition | Free tier target | Paid target | Enterprise target |
|---|---|---|---|---|
| **p95 TTFT** | Time from request accepted to first streamed token emitted | <2s | <1s | <500ms |
| **p99 total latency** | Request accepted to final token (or error) | <15s | <10s | <5s |
| **Error rate** | 5xx + uncaught exceptions / total requests | <1% | <0.5% | <0.1% |
| **Cost per request** | Sum of input + output token cost / request | <$0.15 | <$0.05 | <$0.02 |

TTFT only makes sense if you are streaming. If your app is batch-only, replace
TTFT with p50 total latency at a tighter threshold (<2s paid, <1s enterprise).

## Why these four, not HTTP SLOs

- **HTTP 200s lie.** A request that returns 200 with a `ValidationError`
  serialized into the JSON body is a success to a load balancer and a failure
  to a user. Error-rate must include app-layer exceptions, not just HTTP codes.
- **p95 response time hides TTFT.** A 3s response with streaming feels instant;
  a 3s response without streaming feels broken. TTFT is the real latency SLO
  for streamed apps.
- **Cost is a user-facing concern.** If cost-per-req triples overnight, you
  cannot just absorb it — that is an incident. Cost-per-req belongs in the
  on-call SLO set, not a finance dashboard.

## Recording rules (Prometheus)

Assumes metrics are emitted via the LangSmith callback or equivalent — check
`langchain-observability` for the metric-emission pattern.

```yaml
groups:
  - name: langchain_slo
    interval: 30s
    rules:
      # p99 total latency over 5m
      - record: langchain:p99_latency_5m
        expr: histogram_quantile(0.99, sum(rate(langchain_request_duration_seconds_bucket[5m])) by (le, service))

      # p95 TTFT over 5m
      - record: langchain:p95_ttft_5m
        expr: histogram_quantile(0.95, sum(rate(langchain_ttft_seconds_bucket[5m])) by (le, service))

      # Error rate (5xx + exceptions) over 5m
      - record: langchain:error_rate_5m
        expr: |
          sum(rate(langchain_requests_total{status=~"5..|error"}[5m])) by (service)
            / sum(rate(langchain_requests_total[5m])) by (service)

      # Cost per request over 15m (dollars)
      - record: langchain:cost_per_req_15m
        expr: |
          sum(rate(langchain_request_cost_usd_sum[15m])) by (service)
            / sum(rate(langchain_request_cost_usd_count[15m])) by (service)
```

## Burn-rate alerts (fast + slow)

Google SRE's multi-window multi-burn-rate pattern: a **fast burn** alert fires
on rapid degradation (5min window) so you wake up during real incidents; a
**slow burn** alert (1h window) catches gradual regressions without paging on
a transient blip.

```yaml
  - name: langchain_slo_alerts
    rules:
      # Fast burn: 2% of monthly error budget in 5 minutes
      - alert: LangChainP99LatencyFastBurn
        expr: langchain:p99_latency_5m > 10
        for: 5m
        labels: { severity: page, team: llm }
        annotations:
          summary: "LangChain p99 > 10s (fast burn) on {{ $labels.service }}"
          runbook: "https://runbooks/langchain-incident-runbook#latency"

      # Slow burn: 10% over 1 hour
      - alert: LangChainP99LatencySlowBurn
        expr: avg_over_time(langchain:p99_latency_5m[1h]) > 10
        for: 1h
        labels: { severity: ticket, team: llm }

      # Cost spike — fast only, because cost spikes are acute
      - alert: LangChainCostPerReqSpike
        expr: langchain:cost_per_req_15m > 0.20
        for: 15m
        labels: { severity: page, team: llm }
        annotations:
          runbook: "https://runbooks/langchain-incident-runbook#cost"

      # Error rate
      - alert: LangChainErrorRateFastBurn
        expr: langchain:error_rate_5m > 0.02
        for: 5m
        labels: { severity: page, team: llm }
```

## Per-tier SLO gotchas

- **TTFT requires streaming to be instrumented.** If your callback does not
  record a `first_token_timestamp`, you will alert on "no TTFT samples" which
  is indistinguishable from "TTFT great." Make the metric have a sane default
  and alert on `absent()`.
- **Cost-per-req needs input + output tokens.** Callbacks that only record
  input tokens undercount by 2–10x depending on the chain.
- **Error rate must exclude 429s your retry succeeded on.** Otherwise every
  provider rate-limit blip pages on-call. Record two separate metrics: raw 4xx
  for capacity planning, and "unretried failures" for SLO.

## When to tune the SLO

If you are burning the budget cleanly every month on p99 latency but users are
not complaining, the SLO is too tight — loosen it. If users complain without
any SLO breach, the SLO is missing a dimension (usually TTFT or schema-validity
rate). SLOs are contracts with users, not with Prometheus.
