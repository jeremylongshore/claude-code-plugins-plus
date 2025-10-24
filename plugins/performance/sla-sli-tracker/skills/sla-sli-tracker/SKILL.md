---
name: tracking-service-reliability
description: |
  This skill enables Claude to define and track Service Level Agreements (SLAs), Service Level Indicators (SLIs), and Service Level Objectives (SLOs) for improved service reliability. It is triggered when the user needs to establish, monitor, or analyze service performance metrics. Use this skill when the user mentions "SLA", "SLI", "SLO", "error budget", "service reliability", or "track service performance". The skill helps to define key metrics, set targets, and monitor performance against those targets.
---

## Overview

This skill provides a structured approach to defining and tracking SLAs, SLIs, and SLOs, which are essential for ensuring service reliability. It automates the process of setting performance targets and monitoring actual performance, enabling proactive identification and resolution of potential issues.

## How It Works

1. **SLI Definition**: The skill guides the user to define Service Level Indicators (SLIs) such as availability, latency, error rate, and throughput.
2. **SLO Target Setting**: The skill assists in setting Service Level Objectives (SLOs) by establishing target values for the defined SLIs (e.g., 99.9% availability).
3. **SLA Establishment**: The skill helps in formalizing Service Level Agreements (SLAs), which are customer-facing commitments based on the defined SLOs.

## When to Use This Skill

This skill activates when you need to:
- Define SLAs, SLIs, and SLOs for a service.
- Track service performance against defined objectives.
- Calculate error budgets based on SLOs.

## Examples

### Example 1: Defining SLOs for a New Service

User request: "Create SLOs for our new payment processing service."

The skill will:
1. Prompt the user to define SLIs (e.g., latency, error rate).
2. Assist in setting target values for each SLI (e.g., p99 latency < 100ms, error rate < 0.01%).

### Example 2: Tracking Availability

User request: "Track the availability SLI for the database service."

The skill will:
1. Guide the user in setting up the tracking of the availability SLI.
2. Visualize availability performance against the defined SLO.

## Best Practices

- **Granularity**: Define SLIs that are specific and measurable.
- **Realism**: Set SLOs that are challenging but achievable.
- **Alignment**: Ensure SLAs align with the defined SLOs and business requirements.

## Integration

This skill can be integrated with monitoring tools to automatically collect SLI data and track performance against SLOs. It can also be used in conjunction with alerting systems to trigger notifications when SLO violations occur.