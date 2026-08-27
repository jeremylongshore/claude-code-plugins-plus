---
name: clickhouse-observability
description: |
  Monitor ClickHouse with Prometheus metrics, Grafana dashboards, system table
  queries, and alerting for query performance, merge health, and resource usage.
  Use when setting up ClickHouse monitoring, building Grafana dashboards, or
  configuring alerts for production ClickHouse deployments.
  Trigger with "clickhouse monitoring", "clickhouse metrics", "clickhouse Grafana",
  "clickhouse observability", "monitor clickhouse", "clickhouse Prometheus".
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Observability

## Overview

Set up comprehensive monitoring for ClickHouse using built-in system tables,
Prometheus integration, Grafana dashboards, and alerting rules. The workflow
layers four signal sources: `system.*` tables (always available, zero
dependencies), a Prometheus scrape endpoint, application-level client
instrumentation, and alert rules that fire on the failure modes that actually
page an on-call — high error rate, latency creep, merge backlog, and resource
exhaustion.

Deep configs live in `references/` so this file stays a fast, followable map.

## Prerequisites

- ClickHouse instance with `system.*` table access
- Prometheus (or compatible: Grafana Alloy, Victoria Metrics)
- Grafana for dashboards
- AlertManager or PagerDuty for alerts

## Instructions

### Step 1: Query system tables for a health snapshot

Start with zero dependencies — the `system.*` tables already hold everything.
Run this for an instant server-health read:

```sql
SELECT
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking') AS memory_bytes,
    (SELECT count() FROM system.merges) AS active_merges;
```

Query throughput, insert rates, and per-table part counts (the merge-health
signal), plus a full table of which `system.*` table to poll at what frequency:
[system table queries & reference](references/system-tables.md).

### Step 2: Wire up Prometheus scraping

ClickHouse Cloud exposes a managed Prometheus endpoint (Basic auth with a Cloud
API key); self-hosted uses the built-in `:9363` `/metrics` endpoint enabled in
`config.xml`. Write the scrape config to your `prometheus.yml`. Full Cloud +
self-hosted scrape configs and the `config.xml` block:
[Prometheus scrape config & Grafana dashboards](references/prometheus-grafana.md).

### Step 3: Instrument the application client

Server metrics show what ClickHouse does; client metrics attribute latency,
error codes, and insert volume to your own code. Wrap queries in a `prom-client`
histogram/counter and expose `/metrics`. Full instrumentation + structured
logging: [application-level instrumentation](references/instrumentation.md).

### Step 4: Build Grafana dashboard panels

Panels for QPS, P50/P95/P99 latency, error rate, and insert throughput are in
the [Grafana dashboards reference](references/prometheus-grafana.md). Or import
the official community dashboard: `https://grafana.com/grafana/dashboards/23415`.

### Step 5: Load alert rules

Write Prometheus alert rules for the five production failure modes (error rate,
latency, part count, memory, disk) to a rules file loaded by AlertManager. Full
rule set plus per-alert tuning notes: [Prometheus alert rules](references/alerting.md).

## Output

Applying this skill produces a set of monitoring config artifacts you write to
your infrastructure repo:

- `prometheus.yml` — scrape config targeting your ClickHouse endpoint
- `clickhouse-alerts.yml` — the five-rule alert group loaded by AlertManager
- A Grafana dashboard (imported ID `23415` or the custom JSON panels)
- Client instrumentation exposing `clickhouse_query_duration_seconds`,
  `clickhouse_query_errors_total`, and `clickhouse_insert_rows_total`
- Ad-hoc `system.*` queries for on-demand health snapshots

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics endpoint empty | Prometheus not configured | Enable `/metrics` in config |
| High cardinality alerts | Too many label values | Reduce label cardinality |
| Missing query_log data | Logging disabled | Set `log_queries = 1` in config |
| Dashboard gaps | Scrape interval too long | Use 10-15s scrape interval |

## Examples

**Snapshot server health right now** — run the Step 1 query against any instance
with `system.*` access; no exporter or scrape needed. See
[system-tables.md](references/system-tables.md) for throughput and merge-health
variants.

**Alert when merges fall behind** — the `ClickHouseTooManyParts` rule fires when
a table exceeds 300 active parts for 10 minutes, the classic
inserts-outpacing-merges signal. Full rule + tuning guidance:
[alerting.md](references/alerting.md).

**Attribute slow queries to your service** — wrap calls in `instrumentedQuery()`
so P95 latency and error codes land in Prometheus labeled by query type. See
[instrumentation.md](references/instrumentation.md).

## Resources

- [Prometheus Integration](https://clickhouse.com/docs/integrations/prometheus)
- [ClickHouse Grafana Dashboard](https://grafana.com/grafana/dashboards/23415)
- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [Cloud Monitoring](https://clickhouse.com/blog/clickhouse-cloud-now-supports-prometheus-monitoring)
- For incident response, see the `clickhouse-incident-runbook` skill.
