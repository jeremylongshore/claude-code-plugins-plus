---
name: setting-up-synthetic-monitoring
description: |
  This skill automates the setup of synthetic monitoring for applications. It allows Claude to proactively track performance and availability by configuring uptime, transaction, and API monitoring. Use this skill when the user requests to "set up synthetic monitoring", "configure uptime monitoring", "track application performance", or needs help with "proactive performance tracking". The skill helps to identify critical endpoints and user journeys, design monitoring scenarios, and configure alerts and dashboards.
---

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