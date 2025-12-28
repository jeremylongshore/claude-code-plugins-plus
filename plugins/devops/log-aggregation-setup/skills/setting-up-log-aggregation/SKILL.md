---
name: setting-up-log-aggregation
description: |
  Use when setting up log aggregation solutions using ELK, Loki, or Splunk. Trigger with phrases like "setup log aggregation", "deploy ELK stack", "configure Loki", or "install Splunk". Generates production-ready configurations for data ingestion, processing, storage, and visualization with proper security and scalability.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Log Aggregation Setup

This skill provides automated assistance for log aggregation setup tasks.

## Overview

Sets up centralized log aggregation (ELK/Loki/Splunk) including ingestion pipelines, parsing, retention policies, dashboards, and security controls.

## Prerequisites

Before using this skill, ensure:
- Target infrastructure is identified (Kubernetes, Docker, VMs)
- Storage requirements are calculated based on log volume
- Network connectivity between log sources and aggregation platform
- Authentication mechanism is defined (LDAP, OAuth, basic auth)
- Resource allocation planned (CPU, memory, disk)

## Instructions

1. **Select Platform**: Choose ELK, Loki, Grafana Loki, or Splunk
2. **Configure Ingestion**: Set up log shippers (Filebeat, Promtail, Fluentd)
3. **Define Storage**: Configure retention policies and index lifecycle
4. **Set Up Processing**: Create parsing rules and field extractions
5. **Deploy Visualization**: Configure Kibana/Grafana dashboards
6. **Implement Security**: Enable authentication, encryption, and RBAC
7. **Test Pipeline**: Verify logs flow from sources to visualization

## Output

**ELK Stack (Docker Compose):**
```yaml
# {baseDir}/elk/docker-compose.yml


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
    volumes:
      - es-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

**Loki Configuration:**
```yaml
# {baseDir}/loki/loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
```

## Error Handling

**Out of Memory**
- Error: "Elasticsearch heap space exhausted"
- Solution: Increase heap size in elasticsearch.yml or add more nodes

**Connection Refused**
- Error: "Cannot connect to Elasticsearch"
- Solution: Verify network connectivity and firewall rules

**Index Creation Failed**
- Error: "Failed to create index"
- Solution: Check disk space and index template configuration

**Log Parsing Errors**
- Error: "Failed to parse log line"
- Solution: Review grok patterns or JSON parsing configuration

## Examples

- "Deploy Loki + Promtail on Kubernetes with 14-day retention and basic auth."
- "Set up an ELK stack for app + nginx logs and create a dashboard for 5xx errors."

## Resources

- ELK Stack guide: https://www.elastic.co/guide/
- Loki documentation: https://grafana.com/docs/loki/
- Example configurations in {baseDir}/log-aggregation-examples/
