---
name: tracking-resource-usage
description: Track and optimize resource usage across application stack including CPU, memory, disk, and network I/O. Use when identifying bottlenecks or optimizing costs. Trigger with phrases like "track resource usage", "monitor CPU and memory", or "optimize resource allocation".
version: 1.0.0
allowed-tools: "Read, Bash(top:*), Bash(ps:*), Bash(vmstat:*), Bash(iostat:*), Grep, Glob"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Resource Usage Tracker

This skill provides automated assistance for resource usage tracker tasks.

## Overview

This skill provides a comprehensive solution for monitoring and optimizing resource usage within an application. It leverages the resource-usage-tracker plugin to gather real-time metrics, identify performance bottlenecks, and suggest optimization strategies.

## How It Works

1. **Identify Resources**: The skill identifies the resources to be tracked based on the user's request and the application's configuration (CPU, memory, disk I/O, network I/O, etc.).
2. **Collect Metrics**: The plugin collects real-time metrics for the identified resources, providing a snapshot of current resource consumption.
3. **Analyze Data**: The skill analyzes the collected data to identify performance bottlenecks, resource imbalances, and potential optimization opportunities.
4. **Provide Recommendations**: Based on the analysis, the skill provides specific recommendations for optimizing resource allocation, right-sizing instances, and reducing costs.

## When to Use This Skill

This skill activates when you need to:
- Identify performance bottlenecks in an application.
- Optimize resource allocation to improve efficiency.
- Reduce cloud infrastructure costs by right-sizing instances.
- Monitor resource usage in real-time to detect anomalies.
- Track the impact of code changes on resource consumption.

## Examples

### Example 1: Identifying Memory Leaks

User request: "Track memory usage and identify potential memory leaks."

The skill will:
1. Activate the resource-usage-tracker plugin to monitor memory usage (heap, stack, RSS).
2. Analyze the memory usage data over time to detect patterns indicative of memory leaks.
3. Provide recommendations for identifying and resolving the memory leaks.

### Example 2: Optimizing Database Connection Pool

User request: "Optimize database connection pool utilization."

The skill will:
1. Activate the resource-usage-tracker plugin to monitor database connection pool metrics.
2. Analyze the connection pool utilization data to identify periods of high contention or underutilization.
3. Provide recommendations for adjusting the connection pool size to optimize performance and resource consumption.

## Best Practices

- **Granularity**: Track resource usage at a granular level (e.g., process-level CPU usage) to identify specific bottlenecks.
- **Historical Data**: Analyze historical resource usage data to identify trends and predict future resource needs.
- **Alerting**: Configure alerts to notify you when resource usage exceeds predefined thresholds.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide a comprehensive view of application performance. It can also be used in conjunction with deployment automation tools to automatically right-size instances based on resource usage patterns.

## Prerequisites

- Access to system monitoring tools (top, ps, vmstat, iostat)
- Resource metrics collection infrastructure
- Historical usage data in {baseDir}/metrics/resources/
- Performance baseline definitions

## Instructions

1. Identify resources to track (CPU, memory, disk, network)
2. Collect real-time metrics using system tools
3. Analyze data for bottlenecks and patterns
4. Compare against historical baselines
5. Generate optimization recommendations
6. Provide right-sizing and cost reduction strategies

## Output

- Resource usage reports with trends
- Bottleneck identification and analysis
- Right-sizing recommendations for instances
- Cost optimization suggestions
- Alert configurations for thresholds

## Error Handling

If resource tracking fails:
- Verify system monitoring tool permissions
- Check metrics collection daemon status
- Validate data storage availability
- Ensure network access to monitoring endpoints
- Review baseline data completeness

## Resources

- System performance monitoring guides
- Cloud resource optimization best practices
- CPU and memory profiling techniques
- Infrastructure cost optimization strategies