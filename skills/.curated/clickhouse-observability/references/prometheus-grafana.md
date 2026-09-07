# Prometheus Scrape Config & Grafana Dashboards

## Prometheus Integration

**ClickHouse Cloud** exposes a managed Prometheus endpoint. Authentication uses
HTTP Basic auth with a ClickHouse Cloud API key (`<API_KEY_ID>` as the username,
`<API_KEY_SECRET>` as the password). Store the secret in your secrets manager —
never commit it to the scrape config in plaintext.

```yaml
# prometheus.yml
scrape_configs:
  - job_name: clickhouse-cloud
    metrics_path: /v1/organizations/<ORG_ID>/prometheus
    basic_auth:
      username: <API_KEY_ID>
      password: <API_KEY_SECRET>
    static_configs:
      - targets: ['api.clickhouse.cloud']
    params:
      filtered_metrics: ['true']   # 125 critical metrics only
```

**Self-hosted** — use clickhouse-exporter or built-in metrics endpoint (no auth
on the internal `:9363` endpoint; keep it network-isolated):

```yaml
# prometheus.yml
scrape_configs:
  - job_name: clickhouse
    static_configs:
      - targets: ['clickhouse-server:9363']  # Built-in Prometheus endpoint
    metrics_path: /metrics
```

```xml
<!-- Enable Prometheus endpoint in config.xml -->
<prometheus>
    <endpoint>/metrics</endpoint>
    <port>9363</port>
    <metrics>true</metrics>
    <events>true</events>
    <asynchronous_metrics>true</asynchronous_metrics>
</prometheus>
```

## Grafana Dashboard Panels

```json
{
  "panels": [
    {
      "title": "Query Rate (QPS)",
      "type": "timeseries",
      "targets": [{ "expr": "rate(clickhouse_query_duration_seconds_count[5m])" }]
    },
    {
      "title": "Query Latency P50 / P95 / P99",
      "type": "timeseries",
      "targets": [
        { "expr": "histogram_quantile(0.5, rate(clickhouse_query_duration_seconds_bucket[5m]))" },
        { "expr": "histogram_quantile(0.95, rate(clickhouse_query_duration_seconds_bucket[5m]))" },
        { "expr": "histogram_quantile(0.99, rate(clickhouse_query_duration_seconds_bucket[5m]))" }
      ]
    },
    {
      "title": "Error Rate",
      "type": "stat",
      "targets": [{
        "expr": "rate(clickhouse_query_errors_total[5m]) / rate(clickhouse_query_duration_seconds_count[5m])"
      }]
    },
    {
      "title": "Insert Throughput (rows/sec)",
      "type": "timeseries",
      "targets": [{ "expr": "rate(clickhouse_insert_rows_total[5m])" }]
    }
  ]
}
```

Import the official ClickHouse Grafana dashboard by its Grafana.com dashboard ID:
`https://grafana.com/grafana/dashboards/23415` (23415 is ClickHouse's published
community dashboard ID on grafana.com).
