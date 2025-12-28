---
name: validating-performance-budgets
description: Validate application performance against defined budgets to identify regressions early. Use when checking page load times, bundle sizes, or API response times against thresholds. Trigger with phrases like "validate performance budget", "check performance metrics", or "detect performance regression".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(lighthouse:*), Bash(webpack:*), Bash(performance:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Performance Budget Validator

This skill provides automated assistance for performance budget validator tasks.

## Overview

This skill allows Claude to automatically validate your application's performance against predefined budgets. It helps identify performance regressions and ensures your application maintains optimal performance characteristics.

## How It Works

1. **Analyze Performance Metrics**: Claude analyzes current performance metrics, such as page load times, bundle sizes, and API response times.
2. **Validate Against Budget**: The plugin validates these metrics against predefined performance budget thresholds.
3. **Report Violations**: If any metrics exceed the defined budget, the skill reports violations and provides details on the exceeded thresholds.

## When to Use This Skill

This skill activates when you need to:
- Validate performance against predefined budgets.
- Identify performance regressions in your application.
- Integrate performance budget validation into your CI/CD pipeline.

## Examples

### Example 1: Preventing Performance Regressions

User request: "Validate performance budget for the homepage."

The skill will:
1. Analyze the homepage's performance metrics (load time, bundle size).
2. Compare these metrics against the defined budget.
3. Report any violations, such as exceeding the load time budget.

### Example 2: Integrating with CI/CD

User request: "Run performance budget validation as part of the build process."

The skill will:
1. Execute the performance budget validation command.
2. Check all defined performance metrics against their budgets.
3. Report any violations that would cause the build to fail.

## Best Practices

- **Budget Definition**: Define realistic and achievable performance budgets based on current application performance and user expectations.
- **Metric Selection**: Choose relevant performance metrics that directly impact user experience, such as page load times and API response times.
- **CI/CD Integration**: Integrate performance budget validation into your CI/CD pipeline to automatically detect and prevent performance regressions.

## Integration

This skill can be integrated with other plugins that provide performance metrics, such as website speed test tools or API monitoring services. It can also be used in conjunction with alerting plugins to notify developers of performance budget violations.

## Prerequisites

- Performance budget definitions in {baseDir}/performance-budgets.json
- Access to performance testing tools (Lighthouse, WebPageTest)
- Build output directory for bundle analysis
- Historical performance metrics for comparison

## Instructions

1. Load performance budget configuration
2. Collect current performance metrics (load time, bundle size, API latency)
3. Compare metrics against defined budget thresholds
4. Identify budget violations and severity
5. Generate detailed violation report
6. Provide remediation recommendations

## Output

- Performance budget validation report
- List of metrics exceeding budget thresholds
- Comparison with previous measurements
- Detailed breakdown by metric category
- Actionable recommendations for fixes

## Error Handling

If budget validation fails:
- Verify budget configuration file exists
- Check performance testing tool availability
- Validate metric collection permissions
- Ensure network access to test endpoints
- Review budget threshold definitions

## Resources

- Performance budget best practices
- Lighthouse performance scoring guide
- Bundle size optimization techniques
- CI/CD integration patterns for performance testing