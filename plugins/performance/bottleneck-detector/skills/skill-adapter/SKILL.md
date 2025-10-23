---
name: detecting-performance-bottlenecks
description: |
  This skill enables Claude to detect and resolve performance bottlenecks in applications. It analyzes CPU, memory, I/O, and database performance to identify areas of concern. Use this skill when you need to diagnose slow application performance, optimize resource usage, or proactively prevent performance issues. The skill is triggered by requests to "detect bottlenecks", "analyze performance", "find performance issues", or similar phrases related to performance optimization. It helps uncover root causes and suggest remediation strategies.
---

## Overview

This skill empowers Claude to identify and address performance bottlenecks across different layers of an application. By pinpointing performance issues in CPU, memory, I/O, and database operations, it assists in optimizing resource utilization and improving overall application speed and responsiveness.

## How It Works

1. **Architecture Analysis**: Claude analyzes the application's architecture and data flow to understand potential bottlenecks.
2. **Bottleneck Identification**: The plugin identifies bottlenecks across CPU, memory, I/O, database, lock contention, and resource exhaustion.
3. **Remediation Suggestions**: Claude provides remediation strategies with code examples to resolve the identified bottlenecks.

## When to Use This Skill

This skill activates when you need to:
- Diagnose slow application performance.
- Optimize resource usage (CPU, memory, I/O, database).
- Proactively prevent performance issues.

## Examples

### Example 1: Diagnosing Slow Database Queries

User request: "detect bottlenecks in my database queries"

The skill will:
1. Analyze database query performance and identify slow-running queries.
2. Suggest optimizations like indexing or query rewriting to improve database performance.

### Example 2: Identifying Memory Leaks

User request: "analyze performance and find memory leaks"

The skill will:
1. Profile memory usage patterns to identify potential memory leaks.
2. Provide code examples and recommendations to fix the memory leaks.

## Best Practices

- **Comprehensive Analysis**: Always analyze all potential bottleneck areas (CPU, memory, I/O, database) for a complete picture.
- **Prioritize by Severity**: Focus on addressing the most severe bottlenecks first for maximum impact.
- **Test Thoroughly**: After implementing remediation strategies, thoroughly test the application to ensure the bottlenecks are resolved and no new issues are introduced.

## Integration

This skill can be used in conjunction with code generation plugins to automatically implement the suggested remediation strategies. It also integrates with monitoring and logging tools to provide real-time performance data.