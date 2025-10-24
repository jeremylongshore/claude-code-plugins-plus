---
name: detecting-performance-regressions
description: |
  This skill enables Claude to automatically detect performance regressions in a CI/CD pipeline. It analyzes performance metrics, such as response time and throughput, and compares them against baselines or thresholds. Use this skill when the user requests to "detect performance regressions", "analyze performance metrics for regressions", or "find performance degradation" in a CI/CD environment. The skill is also triggered when the user mentions "baseline comparison", "statistical significance analysis", or "performance budget violations". It helps identify and report performance issues early in the development cycle.
---

## Overview

This skill automates the detection of performance regressions within a CI/CD pipeline. It utilizes various methods, including baseline comparison, statistical analysis, and threshold violation checks, to identify performance degradation. The skill provides insights into potential performance bottlenecks and helps maintain application performance.

## How It Works

1. **Analyze Performance Data**: The plugin gathers performance metrics from the CI/CD environment.
2. **Detect Regressions**: It employs methods like baseline comparison, statistical analysis, and threshold checks to detect regressions.
3. **Report Findings**: The plugin generates a report summarizing the detected performance regressions and their potential impact.

## When to Use This Skill

This skill activates when you need to:
- Identify performance regressions in a CI/CD pipeline.
- Analyze performance metrics for potential degradation.
- Compare current performance against historical baselines.

## Examples

### Example 1: Identifying a Response Time Regression

User request: "Detect performance regressions in the latest build. Specifically, check for increases in response time."

The skill will:
1. Analyze response time metrics from the latest build.
2. Compare the response times against a historical baseline.
3. Report any statistically significant increases in response time that exceed a defined threshold.

### Example 2: Detecting Throughput Degradation

User request: "Analyze throughput for performance regressions after the recent code merge."

The skill will:
1. Gather throughput data (requests per second) from the post-merge CI/CD run.
2. Compare the throughput to pre-merge values, looking for statistically significant drops.
3. Generate a report highlighting any throughput degradation, indicating a potential performance regression.

## Best Practices

- **Define Baselines**: Establish clear and representative performance baselines for accurate comparison.
- **Set Thresholds**: Configure appropriate thresholds for identifying significant performance regressions.
- **Monitor Key Metrics**: Focus on monitoring critical performance metrics relevant to the application's behavior.

## Integration

This skill can be integrated with other CI/CD tools to automatically trigger regression detection upon new builds or code merges. It can also be combined with reporting plugins to generate detailed performance reports.