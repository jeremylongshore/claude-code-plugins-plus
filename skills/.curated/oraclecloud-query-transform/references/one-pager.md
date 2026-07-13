# oraclecloud-query-transform — One-Pager

Query OCI metrics with MQL and create monitoring alarms via the Python SDK.

## The Problem

MQL (Monitoring Query Language) is underdocumented and the console query builder is buggy. This skill provides working MQL queries for the metrics you actually need — CPU, memory, network, disk — via SDK, not console.

## The Solution

This skill provides a complete MQL reference with working Python SDK examples: query syntax breakdown, metric queries for all core infrastructure signals (CPU, memory, network I/O, disk I/O), instance-level filtering, metric discovery, and alarm creation with email notifications. Everything runs via MonitoringClient, bypassing the console entirely.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | SREs, DevOps engineers, and developers building monitoring for OCI workloads |
| **What** | MQL queries for core metrics, reusable query helper, alarm creation with notification topics |
| **When** | Setting up monitoring dashboards, debugging performance issues, creating alerting rules, or replacing console-based query workflows |

## Key Features

1. **MQL cheat sheet** — Ready-to-use queries for CPU, memory, network, and disk with correct syntax
2. **Metric discovery** — List available metrics and namespaces when you do not know what is available
3. **Full alarm pipeline** — Notification topic, email subscription, and alarm creation in one workflow

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
