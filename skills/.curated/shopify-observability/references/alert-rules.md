# Prometheus Alert Rules

Shopify-specific Prometheus alert rules for rate limits, query cost, webhook failures, and API latency.

```yaml
# prometheus/shopify-alerts.yml
groups:
  - name: shopify
    rules:
      - alert: ShopifyRateLimitLow
        expr: shopify_rate_limit_available < 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Shopify rate limit below 100 points for {{ $labels.shop }}"

      - alert: ShopifyHighQueryCost
        expr: histogram_quantile(0.95, rate(shopify_graphql_query_cost_bucket[5m])) > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 Shopify query cost > 500 points"

      - alert: ShopifyWebhookFailures
        expr: rate(shopify_webhooks_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Shopify webhook processing failures > 10%"

      - alert: ShopifyAPILatencyHigh
        expr: histogram_quantile(0.95, rate(shopify_api_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Shopify API P95 latency > 3 seconds"
```
