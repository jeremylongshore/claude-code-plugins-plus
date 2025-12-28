---
name: aggregating-performance-metrics
description: Aggregate and centralize performance metrics from applications, systems, databases, caches, and services. Use when consolidating monitoring data from multiple sources. Trigger with phrases like "aggregate metrics", "centralize monitoring", or "collect performance data".
version: 1.0.0
allowed-tools: "Read, Write, Bash(prometheus:*), Bash(metrics:*), Bash(monitoring:*), Grep"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Metrics Aggregator

This skill provides automated assistance for metrics aggregator tasks.

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

This skill integrates with other plugins that manage infrastructure, deploy applications, and monitor system health. For example, it can be used in conjunction with a deployment plugin to automatically configure metrics collection after a new application deployment.

## Prerequisites

- Access to metrics collection tools (Prometheus, StatsD, CloudWatch)
- Network connectivity to metric sources
- Metrics storage configuration in {baseDir}/metrics/
- Understanding of metrics taxonomy

## Instructions

1. Design consistent metrics naming convention
2. Select appropriate aggregation tool for environment
3. Configure metric collection from all sources
4. Set up centralized storage and retention policies
5. Create dashboards for visualization
6. Define alerts for critical metrics

## Output

- Metrics aggregation configuration files
- Unified naming convention documentation
- Dashboard definitions for key metrics
- Alert rules for performance thresholds
- Integration guides for metric sources

## Error Handling

If metrics aggregation fails:
- Verify network connectivity to sources
- Check authentication credentials
- Validate metrics format compatibility
- Review storage capacity and retention
- Ensure aggregation tool configuration

## Resources

- Prometheus aggregation documentation
- StatsD protocol specifications
- CloudWatch metrics API reference
- Metrics naming best practices