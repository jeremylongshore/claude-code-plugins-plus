---
name: monitoring-error-rates
description: |
  This skill enables Claude to monitor and analyze application error rates to improve reliability. It is used when the user needs to track and understand errors occurring in their application, including HTTP errors, application exceptions, database errors, external API errors, background job errors, and client-side errors. Use this skill when the user asks to "monitor errors", "analyze error rates", "track application errors", or requests help with "error monitoring". It sets up comprehensive error tracking and alerting based on defined thresholds.
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill automates the process of setting up comprehensive error monitoring and alerting for various components of an application. It helps identify, track, and analyze different types of errors, enabling proactive identification and resolution of issues before they impact users.

## How It Works

1. **Analyze Error Sources**: Identifies potential error sources within the application architecture, including HTTP endpoints, database queries, external APIs, background jobs, and client-side code.
2. **Define Monitoring Criteria**: Establishes specific error types and thresholds for each source, such as HTTP status codes (4xx, 5xx), exception types, query timeouts, and API response failures.
3. **Configure Alerting**: Sets up alerts to trigger when error rates exceed defined thresholds, notifying relevant teams or individuals for investigation and remediation.

## When to Use This Skill

This skill activates when you need to:
- Set up error monitoring for a new application.
- Analyze existing error rates and identify areas for improvement.
- Configure alerts to be notified of critical errors in real-time.
- Establish error budgets and track progress towards reliability goals.

## Examples

### Example 1: Setting up Error Monitoring for a Web Application

User request: "Monitor errors in my web application, especially 500 errors and database connection issues."

The skill will:
1. Analyze the web application's architecture to identify potential error sources (e.g., HTTP endpoints, database connections).
2. Configure monitoring for 500 errors and database connection failures, setting appropriate thresholds and alerts.

### Example 2: Analyzing Error Rates in a Background Job Processor

User request: "Analyze error rates for my background job processor. I'm seeing a lot of failed jobs."

The skill will:
1. Focus on the background job processor and identify the types of errors occurring (e.g., task failures, timeouts, resource exhaustion).
2. Analyze the frequency and patterns of these errors to identify potential root causes.

## Best Practices

- **Granularity**: Monitor errors at a granular level to identify specific problem areas.
- **Thresholding**: Set appropriate alert thresholds to avoid alert fatigue and focus on critical issues.
- **Context**: Include relevant context in error messages and alerts to facilitate troubleshooting.

## Integration

This skill can be integrated with other monitoring and alerting tools, such as Prometheus, Grafana, and PagerDuty, to provide a comprehensive view of application health and performance. It can also be used in conjunction with incident management tools to streamline incident response workflows.