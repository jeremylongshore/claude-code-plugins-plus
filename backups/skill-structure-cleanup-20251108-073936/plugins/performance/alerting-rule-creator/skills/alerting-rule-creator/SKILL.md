---
name: creating-alerting-rules
description: |
  This skill enables Claude to create intelligent alerting rules for proactive performance monitoring. It is triggered when the user requests to "create alerts", "define monitoring rules", or "set up alerting". The skill helps define thresholds, routing, and escalation policies, and offers options for multi-category alert creation, including latency, error rate, throughput, resource utilization, availability, and SLO violation alerts. It is useful for Site Reliability Engineers (SREs) and DevOps teams looking to improve system observability.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the creation of comprehensive alerting rules, reducing the manual effort required for performance monitoring. It guides you through defining alert categories, setting intelligent thresholds, and configuring routing and escalation policies. The skill also helps generate runbooks and establish alert testing procedures.

## How It Works

1. **Identify Alert Category**: Determines the type of alert to create (e.g., latency, error rate, resource utilization).
2. **Define Thresholds**: Sets appropriate thresholds to avoid alert fatigue and ensure timely notification of performance issues.
3. **Configure Routing and Escalation**: Establishes routing policies to direct alerts to the appropriate teams and escalation policies for timely response.
4. **Generate Runbook**: Creates a basic runbook with steps to diagnose and resolve the alerted issue.

## When to Use This Skill

This skill activates when you need to:
- Implement performance monitoring for a new service.
- Refine existing alerting rules to reduce false positives.
- Create alerts for specific performance metrics, such as latency or error rate.

## Examples

### Example 1: Setting up Latency Alerts

User request: "create latency alerts for the payment service"

The skill will:
1. Prompt for latency thresholds (e.g., warning and critical).
2. Configure alerts to trigger when latency exceeds defined thresholds.

### Example 2: Creating Error Rate Alerts

User request: "set up alerting for error rate increases in the API gateway"

The skill will:
1. Request the baseline error rate and acceptable deviation.
2. Configure alerts to trigger when the error rate exceeds the defined deviation from the baseline.

## Best Practices

- **Threshold Selection**: Use historical data and statistical analysis to determine appropriate thresholds that minimize false positives and negatives.
- **Alert Routing**: Route alerts to the appropriate teams or individuals based on the alert category and severity.
- **Runbook Creation**: Generate or link to detailed runbooks that provide clear instructions for diagnosing and resolving the alerted issue.

## Integration

This skill can be integrated with other Claude Code plugins to automate incident response workflows. For example, it can trigger automated remediation actions or create tickets in an issue tracking system.