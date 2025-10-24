---
name: profiling-application-performance
description: |
  This skill enables Claude to profile application performance, analyzing CPU usage, memory consumption, and execution time. It is triggered when the user requests performance analysis, bottleneck identification, or optimization recommendations. The skill uses the application-profiler plugin to identify performance bottlenecks and suggest code-level optimizations. Use it when asked to "profile application", "analyze performance", or "find bottlenecks". It is also helpful when the user mentions specific performance metrics like "CPU usage", "memory leaks", or "execution time".
---

## Overview

This skill empowers Claude to analyze application performance, pinpoint bottlenecks, and recommend optimizations. By leveraging the application-profiler plugin, it provides insights into CPU usage, memory allocation, and execution time, enabling targeted improvements.

## How It Works

1. **Identify Application Stack**: Determines the application's technology (e.g., Node.js, Python, Java).
2. **Locate Entry Points**: Identifies main application entry points and critical execution paths.
3. **Analyze Performance Metrics**: Examines CPU usage, memory allocation, and execution time to detect bottlenecks.
4. **Generate Profile**: Compiles the analysis into a comprehensive performance profile, highlighting areas for optimization.

## When to Use This Skill

This skill activates when you need to:
- Analyze application performance for bottlenecks.
- Identify CPU-intensive operations and memory leaks.
- Optimize application execution time.

## Examples

### Example 1: Identifying Memory Leaks

User request: "Analyze my Node.js application for memory leaks."

The skill will:
1. Activate the application-profiler plugin.
2. Analyze the application's memory allocation patterns.
3. Generate a profile highlighting potential memory leaks.

### Example 2: Optimizing CPU Usage

User request: "Profile my Python script and find the most CPU-intensive functions."

The skill will:
1. Activate the application-profiler plugin.
2. Analyze the script's CPU usage.
3. Generate a profile identifying the functions consuming the most CPU time.

## Best Practices

- **Code Instrumentation**: Ensure the application code is instrumented for accurate profiling.
- **Realistic Workloads**: Use realistic workloads during profiling to simulate real-world scenarios.
- **Iterative Optimization**: Apply optimizations iteratively and re-profile to measure improvements.

## Integration

This skill can be used in conjunction with code editing plugins to implement the recommended optimizations directly within the application's source code. It can also integrate with monitoring tools to track performance improvements over time.