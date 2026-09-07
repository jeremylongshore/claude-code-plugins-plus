# Alerting & Dashboards

Prometheus alert rules tuned to Klaviyo's rate-limit and error behavior, plus
the Grafana panels that visualize the metrics emitted by the instrumentation
layer. Tune thresholds to your own traffic pattern — the defaults assume a
moderate steady-state request volume.

## Step 5: Alert Rules (Prometheus)

```yaml
# prometheus/klaviyo-alerts.yml
groups:
  - name: klaviyo
    rules:
      - alert: KlaviyoHighErrorRate
        expr: |
          rate(klaviyo_api_errors_total[5m]) /
          rate(klaviyo_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo API error rate above 5%"
          description: "Error rate: {{ $value | humanizePercentage }}"

      - alert: KlaviyoRateLimited
        expr: |
          increase(klaviyo_api_errors_total{status_code="429"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo rate limit being hit frequently"

      - alert: KlaviyoHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(klaviyo_api_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo API P95 latency above 3 seconds"

      - alert: KlaviyoDown
        expr: |
          increase(klaviyo_api_errors_total{status_code=~"5.."}[5m]) > 20
          and increase(klaviyo_api_requests_total{status="success"}[5m]) == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Klaviyo API appears to be down"

      - alert: KlaviyoRateLimitLow
        expr: klaviyo_rate_limit_remaining < 20
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "Klaviyo rate limit headroom below 20 requests"
```

## Grafana Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| Request Rate | `rate(klaviyo_api_requests_total[5m])` | API call volume |
| Error Rate | `rate(klaviyo_api_errors_total[5m])` | Error trend |
| Latency P50/P95 | `histogram_quantile(0.95, rate(klaviyo_api_duration_seconds_bucket[5m]))` | Performance |
| Rate Limit | `klaviyo_rate_limit_remaining` | Rate limit headroom |
| Error by Code | `topk(5, sum by (status_code) (rate(klaviyo_api_errors_total[5m])))` | Error breakdown |
