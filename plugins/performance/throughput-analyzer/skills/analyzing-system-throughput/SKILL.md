---
name: analyzing-system-throughput
description: Analyze and optimize system throughput including request handling, data processing, and resource utilization. Use when identifying capacity limits or evaluating scaling strategies. Trigger with phrases like "analyze throughput", "optimize capacity", or "identify bottlenecks".
version: 1.0.0
allowed-tools: "Read, Write, Bash(performance:*), Bash(monitoring:*), Grep"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Throughput Analyzer

This skill provides automated assistance for throughput analyzer tasks.

## Overview

This skill allows Claude to analyze system performance and identify areas for throughput optimization. It uses the `throughput-analyzer` plugin to provide insights into request handling, data processing, and resource utilization.

## How It Works

1. **Identify Critical Components**: Determines which system components are most relevant to throughput.
2. **Analyze Throughput Metrics**: Gathers and analyzes current throughput metrics for the identified components.
3. **Identify Limiting Factors**: Pinpoints the bottlenecks and constraints that are hindering optimal throughput.
4. **Evaluate Scaling Strategies**: Explores potential scaling strategies and their impact on overall throughput.

## When to Use This Skill

This skill activates when you need to:
- Analyze system throughput to identify performance bottlenecks.
- Optimize system performance for increased capacity.
- Evaluate scaling strategies to improve throughput.

## Examples

### Example 1: Analyzing Web Server Throughput

User request: "Analyze the throughput of my web server and identify any bottlenecks."

The skill will:
1. Activate the `throughput-analyzer` plugin.
2. Analyze request throughput, data throughput, and resource saturation of the web server.
3. Provide a report identifying potential bottlenecks and optimization opportunities.

### Example 2: Optimizing Data Processing Pipeline

User request: "Optimize the throughput of my data processing pipeline."

The skill will:
1. Activate the `throughput-analyzer` plugin.
2. Analyze data throughput, queue processing, and concurrency limits of the data processing pipeline.
3. Suggest improvements to increase data processing rates and overall throughput.

## Best Practices

- **Component Selection**: Focus the analysis on the most throughput-critical components to avoid unnecessary overhead.
- **Metric Interpretation**: Carefully interpret throughput metrics to accurately identify limiting factors.
- **Scaling Evaluation**: Thoroughly evaluate the potential impact of scaling strategies before implementation.

## Integration

This skill can be used in conjunction with other monitoring and performance analysis tools to gain a more comprehensive understanding of system behavior. It provides a starting point for further investigation and optimization efforts.

## Prerequisites

- Access to throughput metrics in {baseDir}/metrics/throughput/
- System performance monitoring tools
- Historical throughput baselines
- Current capacity and scaling limits

## Instructions

1. Identify critical system components for throughput analysis
2. Collect request and data throughput metrics
3. Analyze resource saturation and queue depths
4. Identify bottlenecks and limiting factors
5. Evaluate horizontal and vertical scaling strategies
6. Generate capacity planning recommendations

## Output

- Throughput analysis reports with current capacity
- Bottleneck identification and root cause analysis
- Resource saturation metrics
- Scaling strategy recommendations
- Capacity planning projections

## Error Handling

If throughput analysis fails:
- Verify metrics collection infrastructure
- Check system monitoring tool access
- Validate historical baseline data
- Ensure performance testing environment
- Review component identification logic

## Resources

- Throughput optimization best practices
- Capacity planning methodologies
- Scaling strategy comparison guides
- Performance bottleneck detection techniques