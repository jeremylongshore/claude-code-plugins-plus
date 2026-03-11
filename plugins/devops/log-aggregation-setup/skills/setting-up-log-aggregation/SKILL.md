---
name: setting-up-log-aggregation
description: |
  Execute use when setting up log aggregation solutions using ELK, Loki, or Splunk. Trigger with phrases like "setup log aggregation", "deploy ELK stack", "configure Loki", or "install Splunk". Generates production-ready configurations for data ingestion, processing, storage, and visualization with proper security and scalability.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Setting Up Log Aggregation

## Overview

Deploy centralized log aggregation platforms (ELK Stack, Grafana Loki, Splunk) with ingestion pipelines, structured parsing, retention policies, visualization dashboards, and alerting. Configure log shippers (Filebeat, Promtail, Fluentd) to collect from applications, containers, and system logs with proper security and scalability.

## Prerequisites

- Target infrastructure identified: Kubernetes, Docker Compose, or VMs
- Storage requirements calculated: estimate daily log volume and multiply by retention period
- Network connectivity between log sources and aggregation platform (typically ports 9200, 3100, 8088)
- Authentication mechanism defined (LDAP, OAuth, API tokens, or basic auth)
- Resource allocation planned: Elasticsearch needs significant heap memory (minimum 4GB per node)

## Instructions

1. Select the log aggregation platform: ELK for full-text search and complex queries, Loki for lightweight Kubernetes-native logging, Splunk for enterprise with advanced analytics
2. Deploy the storage backend: Elasticsearch cluster, Loki with object storage (S3/GCS), or Splunk indexers
3. Configure log shippers on sources: Filebeat for ELK, Promtail for Loki, Fluentd/Fluent Bit for multi-destination
4. Define parsing rules: Logstash grok patterns for unstructured logs, JSON parsing for structured logs, multiline handling for stack traces
5. Set retention policies: Index Lifecycle Management (ILM) for Elasticsearch, chunk retention for Loki, index rotation for Splunk
6. Deploy visualization: Kibana dashboards for ELK, Grafana dashboards for Loki, Splunk Search for Splunk
7. Configure alerting: define log-based alerts for error spikes, application exceptions, and security events
8. Implement RBAC: restrict dashboard access and log visibility by team and environment
9. Test the full pipeline: generate test logs, verify ingestion, confirm parsing, and validate dashboard display

## Output

- Docker Compose or Kubernetes manifests for the log aggregation stack
- Log shipper configuration files (Filebeat YAML, Promtail config, Fluentd conf)
- Parsing and field extraction rules (Logstash pipeline, grok patterns)
- Retention policy configuration (ILM, lifecycle rules)
- Dashboard JSON exports for Kibana or Grafana
- Alert rule definitions for error rate monitoring

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Elasticsearch heap space exhausted` | JVM heap too small for index volume | Increase `ES_JAVA_OPTS` heap size (set to 50% of available RAM, max 32GB) or add nodes |
| `Cannot connect to Elasticsearch` | Network issue or Elasticsearch not started | Verify Elasticsearch is running and healthy; check firewall rules and bind address |
| `Failed to create index` | Disk space full or index template misconfigured | Check disk usage with `df -h`; review index template settings and shard allocation |
| `Failed to parse log line` | Grok pattern mismatch or unexpected log format | Test grok patterns with Kibana Grok Debugger; add fallback pattern for unmatched lines |
| `Promtail: too many open files` | System file descriptor limit too low for log tailing | Increase `ulimit -n` to 65536; reduce the number of watched paths |

## Examples

- "Deploy an ELK stack on Docker Compose with Filebeat collecting Nginx and application logs, Logstash parsing with grok, and a Kibana dashboard for 5xx error monitoring."
- "Set up Loki + Promtail on Kubernetes with 14-day retention, basic auth, and a Grafana dashboard showing logs per namespace."
- "Configure Fluentd to ship logs from 20 application servers to both Elasticsearch (hot storage, 7 days) and S3 (cold storage, 1 year)."

## Resources

- Elastic Stack guide: https://www.elastic.co/guide/
- Grafana Loki: https://grafana.com/docs/loki/latest/
- Fluentd documentation: https://docs.fluentd.org/
- Promtail configuration: https://grafana.com/docs/loki/latest/send-data/promtail/