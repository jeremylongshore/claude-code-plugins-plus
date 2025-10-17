---
name: Tracking Application Response Times
description: |
  This skill enables Claude to track and optimize application response times. It uses the response-time-tracker plugin to monitor API endpoints, database queries, external service calls, frontend rendering, and background job execution. The plugin calculates P50, P95, and P99 percentiles, average and maximum response times. Use this skill when you need to identify performance bottlenecks, monitor SLOs, or receive alerts about performance degradation. Trigger this skill with phrases like "track response times", "optimize latency", or "monitor application performance".
---

## Overview

This skill empowers Claude to proactively monitor and improve application performance by tracking response times across various layers. It provides detailed metrics and insights to identify and resolve performance bottlenecks.

## How It Works

1. **Initiate Tracking**: The user requests response time tracking.
2. **Configure Monitoring**: The plugin automatically begins monitoring API endpoints, database queries, external service calls, frontend rendering, and background jobs.
3. **Report Metrics**: The plugin generates reports including P50, P95, P99 percentiles, average, and maximum response times.

## When to Use This Skill

This skill activates when you need to:
- Identify performance bottlenecks in your application.
- Monitor service level objectives (SLOs) related to response times.
- Receive alerts about performance degradation.

## Examples

### Example 1: Diagnosing Slow API Endpoint

User request: "Track response times for the user authentication API endpoint."

The skill will:
1. Activate the response-time-tracker plugin.
2. Monitor the specified API endpoint and report response time metrics, highlighting potential bottlenecks.

### Example 2: Monitoring Database Query Performance

User request: "Monitor database query performance for the product catalog."

The skill will:
1. Activate the response-time-tracker plugin.
2. Track the execution time of database queries related to the product catalog and provide performance insights.

## Best Practices

- **Granularity**: Track response times at a granular level (e.g., individual API endpoints, specific database queries) for more precise insights.
- **Alerting**: Configure alerts for significant deviations from baseline performance to proactively address potential issues.
- **Contextualization**: Correlate response time data with other metrics (e.g., CPU usage, memory consumption) to identify root causes.

## Integration

This skill can be integrated with other monitoring and alerting tools to provide a comprehensive view of application performance. It can also be used in conjunction with optimization tools to automatically address identified bottlenecks.