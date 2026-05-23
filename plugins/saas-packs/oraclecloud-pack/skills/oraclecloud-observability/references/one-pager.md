# oraclecloud-observability — One-Pager

Set up programmatic monitoring, logging, and alarms for OCI resources without depending on the Console.

## The Problem

OCI Monitoring, Logging, and Alarms exist but the console makes them hard to find and configure. The status page doesn't even acknowledge outages (London Jan 2026). Teams discover infrastructure problems from customers instead of from alerts because the monitoring setup is too complex to get right through the Console UI alone.

## The Solution

This skill sets up programmatic monitoring you can actually trust. It covers metric queries with MonitoringClient, alarm creation with threshold-based rules, custom application metric publishing, notification topic setup with email subscriptions, log searching for error investigation, and HTTP health check probes — all through the Python SDK so your observability config is version-controlled and reproducible.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and SREs responsible for OCI infrastructure reliability |
| **What** | Code-driven observability: metric queries, alarm rules, custom metrics, notification topics, log search, and health checks |
| **When** | Setting up monitoring for new infrastructure, adding custom application metrics, or replacing Console-only alarm config with code |

## Key Features

1. **Metric queries** — MQL queries via `oci.monitoring.MonitoringClient` for CPU, memory, network, and custom metrics
2. **Alarm automation** — SDK-created alarms with notification delivery so monitoring config lives in code, not the Console
3. **Custom metrics** — Push application-level data into OCI Monitoring for unified alerting

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
