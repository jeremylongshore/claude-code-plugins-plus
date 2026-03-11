---
name: deploying-monitoring-stacks
description: |
  Monitor use when deploying monitoring stacks including Prometheus, Grafana, and Datadog. Trigger with phrases like "deploy monitoring stack", "setup prometheus", "configure grafana", or "install datadog agent". Generates production-ready configurations with metric collection, visualization dashboards, and alerting rules.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Deploying Monitoring Stacks

## Overview

Deploy production monitoring stacks (Prometheus + Grafana, Datadog, or Victoria Metrics) with metric collection, custom dashboards, and alerting rules. Configure exporters, scrape targets, recording rules, and notification channels for comprehensive infrastructure and application observability.

## Prerequisites

- Target infrastructure identified: Kubernetes cluster, Docker hosts, or bare-metal servers
- Metric endpoints accessible from the monitoring platform (application `/metrics`, node exporters)
- Storage backend capacity planned for time-series data (Prometheus TSDB, Thanos, or Cortex for long-term)
- Alert notification channels defined: Slack webhook, PagerDuty integration key, or email SMTP
- Helm 3+ for Kubernetes deployments using kube-prometheus-stack or similar charts

## Instructions

1. Select the monitoring platform: Prometheus + Grafana for open-source self-hosted, Datadog for managed SaaS, Victoria Metrics for high-cardinality workloads
2. Deploy the monitoring stack: `helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack` or Docker Compose for non-Kubernetes
3. Install exporters on monitored systems: node-exporter for host metrics, kube-state-metrics for Kubernetes object states, application-specific exporters
4. Configure scrape targets in `prometheus.yml`: define job names, scrape intervals, and relabeling rules for service discovery
5. Create recording rules for frequently queried aggregations to reduce dashboard query load
6. Define alerting rules with meaningful thresholds: high CPU (>80% for 5m), high memory (>90%), error rate (>1%), latency P99 (>500ms)
7. Configure Alertmanager with routing, grouping, and notification channels (Slack, PagerDuty, email)
8. Build Grafana dashboards: RED metrics (Rate, Errors, Duration) for services, USE metrics (Utilization, Saturation, Errors) for resources
9. Set up data retention: configure TSDB retention period (15-30 days local), set up Thanos/Cortex for long-term storage if needed
10. Test the full pipeline: trigger a test alert and verify notification delivery

## Output

- Helm values file or Docker Compose for the monitoring stack
- Prometheus configuration with scrape targets, recording rules, and alerting rules
- Alertmanager configuration with routing tree and notification receivers
- Grafana dashboard JSON files for infrastructure and application metrics
- Exporter deployment manifests (node-exporter DaemonSet, application ServiceMonitor)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `No data points in dashboard` | Scrape target not reachable or metric name wrong | Check `Targets` page in Prometheus UI; verify service discovery and metric name |
| `Too many time series (high cardinality)` | Labels with unbounded values (user IDs, request IDs) | Remove high-cardinality labels with `metric_relabel_configs`; use recording rules for aggregation |
| `Alert condition met but no notification` | Alertmanager routing or receiver misconfigured | Verify Alertmanager config with `amtool check-config`; test receiver with `amtool silence` |
| `Prometheus OOMKilled` | Insufficient memory for series count | Increase memory limits; reduce scrape targets or retention; add WAL compression |
| `Grafana datasource connection failed` | Wrong Prometheus URL or network policy blocking access | Verify datasource URL in Grafana; check Kubernetes service name and port; review network policies |

## Examples

- "Deploy kube-prometheus-stack on Kubernetes with alerts for node CPU > 80%, pod restart count > 5, and API error rate > 1%, sending to Slack."
- "Set up Prometheus + Grafana on Docker Compose for monitoring 10 application servers with node-exporter and custom application metrics."
- "Create Grafana dashboards for the four golden signals (latency, traffic, errors, saturation) for a microservices application."

## Resources

- Prometheus documentation: https://prometheus.io/docs/
- Grafana documentation: https://grafana.com/docs/grafana/latest/
- kube-prometheus-stack: https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack
- Alerting best practices: https://prometheus.io/docs/practices/alerting/
- Datadog documentation: https://docs.datadoghq.com/