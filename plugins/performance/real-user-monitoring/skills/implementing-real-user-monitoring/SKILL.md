---
name: implementing-real-user-monitoring
description: Implement Real User Monitoring (RUM) to capture actual user performance data including Core Web Vitals and page load times. Use when setting up user experience monitoring or tracking custom performance events. Trigger with phrases like "setup RUM", "track Core Web Vitals", or "monitor real user performance".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(npm:*), Bash(rum:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Real User Monitoring

This skill provides automated assistance for real user monitoring tasks.

## Overview

This skill streamlines the process of setting up Real User Monitoring (RUM) for web applications. It guides you through the essential steps of choosing a platform, defining metrics, and implementing the tracking code to capture valuable user experience data.

## How It Works

1. **Platform Selection**: Helps you consider available RUM platforms (e.g., Google Analytics, Datadog RUM, New Relic).
2. **Instrumentation Design**: Guides you in defining the key performance metrics to track, including Core Web Vitals and custom events.
3. **Tracking Code Implementation**: Assists in implementing the necessary JavaScript code to collect and transmit performance data.

## When to Use This Skill

This skill activates when you need to:
- Implement Real User Monitoring on a website or web application.
- Track Core Web Vitals (LCP, FID, CLS) to improve user experience.
- Monitor page load times (FCP, TTI, TTFB) for performance optimization.

## Examples

### Example 1: Setting up RUM for a new website

User request: "setup RUM for my new website"

The skill will:
1. Guide the user through selecting a RUM platform.
2. Provide code snippets for implementing basic tracking.

### Example 2: Tracking custom performance metrics

User request: "I want to track how long it takes users to complete a purchase"

The skill will:
1. Help define a custom performance metric for purchase completion time.
2. Generate JavaScript code to track the metric.

## Best Practices

- **Privacy Compliance**: Ensure compliance with privacy regulations (e.g., GDPR, CCPA) when collecting user data.
- **Sampling**: Implement sampling to reduce data volume and impact on performance.
- **Error Handling**: Implement robust error handling to prevent tracking code from breaking the website.

## Integration

This skill can be used in conjunction with other monitoring and analytics tools to provide a comprehensive view of application performance.

## Prerequisites

- Access to web application frontend code in {baseDir}/
- RUM platform account (Google Analytics, Datadog, New Relic)
- Understanding of Core Web Vitals metrics
- Privacy compliance documentation (GDPR, CCPA)

## Instructions

1. Select appropriate RUM platform for requirements
2. Define key metrics to track (Core Web Vitals, custom events)
3. Implement tracking code in application frontend
4. Configure data sampling and privacy settings
5. Set up dashboards for metric visualization
6. Define alerts for performance degradation

## Output

- RUM implementation code snippets
- Platform configuration documentation
- Custom event tracking examples
- Dashboard definitions for key metrics
- Privacy compliance checklist

## Error Handling

If RUM implementation fails:
- Verify platform API credentials
- Check JavaScript bundle integration
- Validate metric collection permissions
- Review privacy consent configuration
- Ensure network connectivity for data transmission

## Resources

- Core Web Vitals measurement guide
- RUM platform documentation
- Privacy compliance best practices
- Performance monitoring strategies