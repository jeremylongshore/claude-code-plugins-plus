---
name: creating-apm-dashboards
description: |
  This skill enables AI assistant to create application performance monitoring (apm) dashboards. it is triggered when the user requests the creation of a new apm dashboard, monitoring dashboard, or a dashboard for application performance. the skill helps ... Use when generating or creating new content. Trigger with phrases like 'generate', 'create', or 'scaffold'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Apm Dashboard Creator

This skill provides automated assistance for apm dashboard creator tasks.

## Overview

This skill automates the creation of Application Performance Monitoring (APM) dashboards, providing a structured approach to visualizing critical application metrics. By defining key performance indicators and generating dashboard configurations, this skill simplifies the process of monitoring application health and performance.

## How It Works

1. **Identify Requirements**: Determine the specific metrics and visualizations needed for the APM dashboard based on the user's request.
2. **Define Dashboard Components**: Select relevant components such as golden signals (latency, traffic, errors, saturation), request metrics, resource utilization, database metrics, cache metrics, business metrics, and error tracking.
3. **Generate Configuration**: Create the dashboard configuration file based on the selected components and user preferences.
4. **Deploy Dashboard**: Deploy the generated configuration to the target monitoring platform (e.g., Grafana, Datadog).

## When to Use This Skill

This skill activates when you need to:
- Create a new APM dashboard for an application.
- Define key metrics and visualizations for monitoring application performance.
- Generate dashboard configurations for Grafana, Datadog, or other monitoring platforms.

## Examples

### Example 1: Creating a Grafana Dashboard

User request: "Create a Grafana dashboard for monitoring my web application's performance."

The skill will:
1. Identify the need for a Grafana dashboard focused on web application performance.
2. Define dashboard components including request rate, response times, error rates, and resource utilization (CPU, memory).
3. Generate a Grafana dashboard configuration file with pre-defined visualizations for these metrics.

### Example 2: Setting up a Datadog Dashboard

User request: "Set up a Datadog dashboard to track the golden signals for my microservice."

The skill will:
1. Identify the need for a Datadog dashboard focused on golden signals.
2. Define dashboard components including latency, traffic, errors, and saturation metrics.
3. Generate a Datadog dashboard configuration file with pre-defined visualizations for these metrics.

## Best Practices

- **Specificity**: Provide detailed information about the application and metrics to be monitored.
- **Platform Selection**: Clearly specify the target monitoring platform (Grafana, Datadog, etc.) to ensure compatibility.
- **Iteration**: Review and refine the generated dashboard configuration to meet specific monitoring needs.

## Integration

This skill can be integrated with other plugins that manage infrastructure or application deployment to automatically create APM dashboards as part of the deployment process. It can also work with alerting plugins to define alert rules based on the metrics displayed in the generated dashboards.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Resources

- Project documentation
- Related skills and commands