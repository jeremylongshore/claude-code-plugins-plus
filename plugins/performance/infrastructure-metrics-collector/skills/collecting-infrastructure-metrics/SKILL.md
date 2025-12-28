---
name: collecting-infrastructure-metrics
description: Collect comprehensive infrastructure performance metrics across compute, storage, network, containers, load balancers, and databases. Use when monitoring system performance or troubleshooting infrastructure issues. Trigger with phrases like "collect infrastructure metrics", "monitor server performance", or "track system resources".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(metrics:*), Bash(monitoring:*), Bash(system:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Infrastructure Metrics Collector

This skill provides automated assistance for infrastructure metrics collector tasks.

## Overview

This skill automates the process of setting up infrastructure metrics collection. It identifies key performance indicators (KPIs) across various infrastructure layers, configures agents to collect these metrics, and assists in setting up central aggregation and visualization.

## How It Works

1. **Identify Infrastructure Layers**: Determines the infrastructure layers to monitor (compute, storage, network, containers, load balancers, databases).
2. **Configure Metrics Collection**: Sets up agents (Prometheus, Datadog, CloudWatch) to collect metrics from the identified layers.
3. **Aggregate Metrics**: Configures central aggregation of the collected metrics for analysis and visualization.
4. **Create Dashboards**: Generates infrastructure dashboards for health monitoring, performance analysis, and capacity tracking.

## When to Use This Skill

This skill activates when you need to:
- Monitor the performance of your infrastructure.
- Identify bottlenecks in your system.
- Set up dashboards for real-time monitoring.

## Examples

### Example 1: Setting up basic monitoring

User request: "Collect infrastructure metrics for my web server."

The skill will:
1. Identify compute, storage, and network layers relevant to the web server.
2. Configure Prometheus to collect CPU, memory, disk I/O, and network bandwidth metrics.

### Example 2: Troubleshooting database performance

User request: "I'm seeing slow database queries. Can you help me monitor the database performance?"

The skill will:
1. Identify the database layer and relevant metrics such as connection pool usage, replication lag, and cache hit rates.
2. Configure Datadog to collect these metrics and create a dashboard to visualize performance trends.

## Best Practices

- **Agent Selection**: Choose the appropriate agent (Prometheus, Datadog, CloudWatch) based on your existing infrastructure and monitoring tools.
- **Metric Granularity**: Balance the granularity of metrics collection with the storage and processing overhead. Collect only the essential metrics for your use case.
- **Alerting**: Configure alerts based on thresholds for key metrics to proactively identify and address performance issues.

## Integration

This skill can be integrated with other plugins for deployment, configuration management, and alerting to provide a comprehensive infrastructure management solution. For example, it can be used with a deployment plugin to automatically configure metrics collection after deploying new infrastructure.

## Prerequisites

- Access to infrastructure monitoring systems (Prometheus, Datadog, CloudWatch)
- System permissions for metrics agent installation
- Network access to monitored infrastructure components
- Storage for metrics data in {baseDir}/metrics/

## Instructions

1. Identify infrastructure layers to monitor (compute, storage, network, databases)
2. Select appropriate metrics collection agent based on environment
3. Configure agent with target endpoints and metric types
4. Set up central aggregation for collected metrics
5. Create dashboards for visualization
6. Configure alerts for critical metrics thresholds

## Output

- Metrics collection configuration files
- Agent installation and setup scripts
- Dashboard definitions for infrastructure monitoring
- Metric export configurations
- Alert rules for critical thresholds

## Error Handling

If metrics collection fails:
- Verify agent installation and permissions
- Check network connectivity to targets
- Validate authentication credentials
- Review firewall and security group rules
- Confirm metric endpoint availability

## Resources

- Prometheus documentation for metric collection
- Datadog agent configuration guides
- AWS CloudWatch metrics reference
- Infrastructure monitoring best practices