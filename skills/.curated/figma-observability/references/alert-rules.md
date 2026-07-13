# Step 3: Alert Rules

Deep-dive reference for the `figma-observability` skill — extracted from the 'Step 3: Alert Rules' step of the workflow.

```yaml
# prometheus-alerts.yml
groups:
  - name: figma
    rules:
      - alert: FigmaHighErrorRate
        expr: |
          rate(figma_api_requests_total{status=~"4..|5.."}[5m])
          / rate(figma_api_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Figma API error rate > 5% for 5 minutes"

      - alert: FigmaRateLimited
        expr: figma_rate_limit_remaining < 5
        for: 1m
        labels: { severity: warning }
        annotations:
          summary: "Figma rate limit nearly exhausted"

      - alert: FigmaHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(figma_api_request_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Figma API P95 latency > 5 seconds"

      - alert: FigmaAuthFailure
        expr: figma_api_requests_total{status="403"} > 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Figma auth failures detected (possible expired PAT)"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
