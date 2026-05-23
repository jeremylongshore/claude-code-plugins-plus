# Alert Configuration

## Alert Configuration

### Prometheus AlertManager Rules

```yaml
# supabase_alerts.yaml
groups:
  - name: supabase_alerts
    rules:
      - alert: SupabaseHighErrorRate
        expr: |
          rate(supabase_errors_total[5m]) /
          rate(supabase_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Supabase error rate > 5%"

      - alert: SupabaseHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(supabase_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Supabase P95 latency > 2s"

      - alert: SupabaseDown
        expr: up{job="supabase"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Supabase integration is down"
```
