---
description: Use when deploying monitoring stacks including Prometheus, Grafana, and Datadog. Trigger with phrases like "deploy monitoring stack", "setup prometheus", "configure grafana", or "install datadog agent". Generates production-ready configurations with metric collection, visualization dashboards, and alerting rules.
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(docker:*)
- Bash(kubectl:*)
name: deploying-monitoring-stacks
license: MIT
version: 1.0.0
---

## Prerequisites

Before using this skill, ensure:
- Target infrastructure is identified (Kubernetes, Docker, bare metal)
- Metric endpoints are accessible from monitoring platform
- Storage backend is configured for time-series data
- Alert notification channels are defined (email, Slack, PagerDuty)
- Resource requirements are calculated based on scale

## Instructions

1. **Select Platform**: Choose Prometheus/Grafana, Datadog, or hybrid approach
2. **Deploy Collectors**: Install exporters and agents on monitored systems
3. **Configure Scraping**: Define metric collection endpoints and intervals
4. **Set Up Storage**: Configure retention policies and data compaction
5. **Create Dashboards**: Build visualization panels for key metrics
6. **Define Alerts**: Create alerting rules with appropriate thresholds
7. **Test Monitoring**: Verify metrics flow and alert triggering

## Output

**Prometheus + Grafana (Kubernetes):**
```yaml
# {baseDir}/monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.retention.time=30d'
        ports:
        - containerPort: 9090
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "Application Metrics",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Error Handling

**Metrics Not Appearing**
- Error: "No data points"
- Solution: Verify scrape targets are accessible and returning metrics

**High Cardinality**
- Error: "Too many time series"
- Solution: Reduce label combinations or increase Prometheus resources

**Alert Not Firing**
- Error: "Alert condition met but no notification"
- Solution: Check Alertmanager configuration and notification channels

**Dashboard Load Failure**
- Error: "Failed to load dashboard"
- Solution: Verify Grafana datasource configuration and permissions

## Resources

- Prometheus documentation: https://prometheus.io/docs/
- Grafana documentation: https://grafana.com/docs/
- Example dashboards in {baseDir}/monitoring-examples/
