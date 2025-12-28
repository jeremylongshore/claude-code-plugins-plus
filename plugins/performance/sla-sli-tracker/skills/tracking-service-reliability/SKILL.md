---
name: tracking-service-reliability
description: Define and track SLAs, SLIs, and SLOs for service reliability including availability, latency, and error rates. Use when establishing reliability targets or monitoring service health. Trigger with phrases like "define SLOs", "track SLI metrics", or "calculate error budget".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(monitoring:*), Bash(metrics:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Sla Sli Tracker

This skill provides automated assistance for sla sli tracker tasks.

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

## Prerequisites

- SLI definitions stored in {baseDir}/slos/sli-definitions.yaml
- Access to monitoring and metrics systems
- Historical performance data for baseline
- Business requirements for service reliability

## Instructions

1. Define Service Level Indicators (availability, latency, error rate, throughput)
2. Set Service Level Objectives with target values (e.g., 99.9% availability)
3. Formalize Service Level Agreements with customer commitments
4. Configure automated SLI data collection
5. Calculate error budgets based on SLOs
6. Track performance and alert on SLO violations

## Output

- SLI/SLO/SLA definition documents
- Real-time SLI metric dashboards
- Error budget calculations and burn rate
- SLO compliance reports
- Alerting configurations for violations

## Error Handling

If SLI/SLO tracking fails:
- Verify SLI definition completeness
- Check metric collection infrastructure
- Validate data accuracy and granularity
- Ensure alerting system connectivity
- Review error budget calculation logic

## Resources

- Google SRE book on SLIs and SLOs
- Error budget implementation guides
- Service reliability engineering practices
- SLO definition templates and examples