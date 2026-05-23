# Alert Configuration

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# vercel_alerts.yaml
groups:
  - name: vercel_alerts
    rules:
      - alert: VercelHighErrorRate
        expr: |
          rate(vercel_errors_total[5m]) /
          rate(vercel_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Vercel error rate > 5%"

      - alert: VercelHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(vercel_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Vercel P95 latency > 2s"

      - alert: VercelDown
        expr: up{job="vercel"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Vercel integration is down"
```
