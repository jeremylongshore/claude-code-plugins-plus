---
name: monitoring-cpu-usage
description: |
  This skill enables Claude to monitor and analyze CPU usage patterns within applications. It helps identify CPU hotspots, analyze algorithmic complexity, and detect blocking operations. Use this skill when the user asks to "monitor CPU usage", "optimize CPU performance", "analyze CPU load", or "find CPU bottlenecks". It assists in identifying inefficient loops, regex performance issues, and provides optimization recommendations. This skill is designed for improving application performance by addressing CPU-intensive operations.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to analyze code for CPU-intensive operations, offering detailed optimization recommendations to improve processor utilization. By pinpointing areas of high CPU usage, it facilitates targeted improvements for enhanced application performance.

## How It Works

1. **Initiate CPU Monitoring**: Claude activates the `cpu-usage-monitor` plugin.
2. **Code Analysis**: The plugin analyzes the codebase for computationally expensive operations, synchronous blocking calls, inefficient loops, and regex patterns.
3. **Optimization Recommendations**: Claude provides a detailed report outlining areas for optimization, including suggestions for algorithmic improvements, asynchronous processing, and regex optimization.

## When to Use This Skill

This skill activates when you need to:
- Identify CPU bottlenecks in your application.
- Optimize application performance by reducing CPU load.
- Analyze code for computationally intensive operations.

## Examples

### Example 1: Identifying CPU Hotspots

User request: "Monitor CPU usage in my Python script and suggest optimizations."

The skill will:
1. Analyze the provided Python script for CPU-intensive functions.
2. Identify potential bottlenecks such as inefficient loops or complex regex patterns.
3. Provide recommendations for optimizing the code, such as using more efficient algorithms or asynchronous operations.

### Example 2: Analyzing Algorithmic Complexity

User request: "Analyze the CPU load of this Java code and identify areas with high algorithmic complexity."

The skill will:
1. Analyze the provided Java code, focusing on algorithmic complexity (e.g., O(n^2) or worse).
2. Pinpoint specific methods or sections of code with high complexity.
3. Suggest alternative algorithms or data structures to improve performance.

## Best Practices

- **Targeted Analysis**: Focus the analysis on specific sections of code known to be CPU-intensive.
- **Asynchronous Operations**: Consider using asynchronous operations to prevent blocking the main thread.
- **Regex Optimization**: Carefully review and optimize regular expressions for performance.

## Integration

This skill can be used in conjunction with other code analysis and refactoring tools to implement the suggested optimizations. It can also be integrated into CI/CD pipelines to automatically monitor CPU usage and identify performance regressions.