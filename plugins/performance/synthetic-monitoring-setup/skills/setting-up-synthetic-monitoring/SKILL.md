---
name: setting-up-synthetic-monitoring
description: Setup synthetic monitoring for proactive performance tracking including uptime checks, transaction monitoring, and API health. Use when implementing availability monitoring or tracking critical user journeys. Trigger with phrases like "setup synthetic monitoring", "monitor uptime", or "configure health checks".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(curl:*), Bash(monitoring:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Synthetic Monitoring Setup

This skill provides automated assistance for synthetic monitoring setup tasks.

## Overview

This skill streamlines the process of setting up synthetic monitoring, enabling proactive performance tracking for applications. It guides the user through defining key monitoring scenarios and configuring alerts to ensure optimal application performance and availability.

## How It Works

1. **Identify Monitoring Needs**: Determine the critical endpoints, user journeys, and APIs to monitor based on the user's application requirements.
2. **Design Monitoring Scenarios**: Create specific monitoring scenarios for uptime, transactions, and API performance, including frequency and location.
3. **Configure Monitoring**: Set up the synthetic monitoring tool with the designed scenarios, including alerts and dashboards for performance visualization.

## When to Use This Skill

This skill activates when you need to:
- Implement uptime monitoring for a web application.
- Track the performance of critical user journeys through transaction monitoring.
- Monitor the response time and availability of API endpoints.

## Examples

### Example 1: Setting up Uptime Monitoring

User request: "Set up uptime monitoring for my website example.com."

The skill will:
1. Identify example.com as the target endpoint.
2. Configure uptime monitoring to check the availability of example.com every 5 minutes from multiple locations.

### Example 2: Monitoring API Performance

User request: "Configure API monitoring for the /users endpoint of my application."

The skill will:
1. Identify the /users endpoint as the target for API monitoring.
2. Set up monitoring to track the response time and status code of the /users endpoint every minute.

## Best Practices

- **Prioritize Critical Endpoints**: Focus on monitoring the most critical endpoints and user journeys that directly impact user experience.
- **Set Realistic Thresholds**: Configure alerts with realistic thresholds to avoid false positives and ensure timely notifications.
- **Regularly Review and Adjust**: Periodically review the monitoring configuration and adjust scenarios and thresholds based on application changes and performance trends.

## Integration

This skill can be integrated with other plugins for incident management and alerting, such as those that handle notifications via Slack or PagerDuty, allowing for automated incident response workflows based on synthetic monitoring results.

## Prerequisites

- Access to synthetic monitoring platform (Pingdom, Datadog, New Relic)
- List of critical endpoints and user journeys in {baseDir}/monitoring/endpoints.yaml
- Alerting infrastructure configuration
- Geographic monitoring location requirements

## Instructions

1. Identify critical endpoints and user journeys to monitor
2. Design monitoring scenarios (uptime, transactions, API checks)
3. Configure monitoring frequency and locations
4. Set up performance and availability thresholds
5. Configure alerting for failures and degradation
6. Create dashboards for monitoring visualization

## Output

- Synthetic monitoring configuration files
- Uptime check definitions for endpoints
- Transaction monitoring scripts
- Alert rule configurations
- Dashboard definitions for monitoring status

## Error Handling

If synthetic monitoring setup fails:
- Verify monitoring platform credentials
- Check endpoint accessibility from monitoring locations
- Validate transaction script syntax
- Ensure alert channel configuration
- Review threshold definitions

## Resources

- Synthetic monitoring best practices
- Uptime monitoring service documentation
- Transaction monitoring script examples
- Alert threshold tuning guides