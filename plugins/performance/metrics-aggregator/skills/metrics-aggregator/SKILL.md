---
name: aggregating-performance-metrics
description: |
  This skill enables Claude to aggregate and centralize performance metrics from various sources. It is used when the user needs to consolidate metrics from applications, systems, databases, caches, queues, and external services into a central location for monitoring and analysis. The skill is triggered by requests to "aggregate metrics", "centralize performance metrics", or similar phrases related to metrics aggregation and monitoring. It facilitates designing a metrics taxonomy, choosing appropriate aggregation tools, and setting up dashboards and alerts.
allowed-tools: Read, Write, Bash, Grep
version: 1.0.0
---

## Overview

This skill empowers Claude to streamline performance monitoring by aggregating metrics from diverse systems into a unified view. It simplifies the process of collecting, centralizing, and analyzing performance data, leading to improved insights and faster issue resolution.

## How It Works

1. **Metrics Taxonomy Design**: Claude assists in defining a clear and consistent naming convention for metrics across all systems.
2. **Aggregation Tool Selection**: Claude helps select the appropriate metrics aggregation tool (e.g., Prometheus, StatsD, CloudWatch) based on the user's environment and requirements.
3. **Configuration and Integration**: Claude guides the configuration of the chosen aggregation tool and its integration with various data sources.
4. **Dashboard and Alert Setup**: Claude helps set up dashboards for visualizing metrics and defining alerts for critical performance indicators.

## When to Use This Skill

This skill activates when you need to:
- Centralize performance metrics from multiple applications and systems.
- Design a consistent metrics naming convention.
- Choose the right metrics aggregation tool for your needs.
- Set up dashboards and alerts for performance monitoring.

## Examples

### Example 1: Centralizing Application and System Metrics

User request: "Aggregate application and system metrics into Prometheus."

The skill will:
1. Guide the user in defining metrics for applications (e.g., request latency, error rates) and systems (e.g., CPU usage, memory utilization).
2. Help configure Prometheus to scrape metrics from the application and system endpoints.

### Example 2: Setting Up Alerts for Database Performance

User request: "Centralize database metrics and set up alerts for slow queries."

The skill will:
1. Help the user define metrics for database performance (e.g., query execution time, connection pool usage).
2. Guide the user in configuring the aggregation tool to collect these metrics from the database.
3. Assist in setting up alerts in the aggregation tool to notify the user when query execution time exceeds a defined threshold.

## Best Practices

- **Naming Conventions**: Use a consistent and well-defined naming convention for all metrics to ensure clarity and ease of analysis.
- **Granularity**: Choose an appropriate level of granularity for metrics to balance detail and storage requirements.
- **Retention Policies**: Define retention policies for metrics to manage storage space and ensure data is available for historical analysis.

## Integration

This skill integrates with other Claude Code plugins that manage infrastructure, deploy applications, and monitor system health. For example, it can be used in conjunction with a deployment plugin to automatically configure metrics collection after a new application deployment.