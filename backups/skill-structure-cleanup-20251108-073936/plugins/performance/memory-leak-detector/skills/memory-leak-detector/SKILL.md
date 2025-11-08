---
name: detecting-memory-leaks
description: |
  This skill enables Claude to detect potential memory leaks and analyze memory usage patterns in code. It is triggered when the user requests "detect memory leaks", "analyze memory usage", or similar phrases related to memory leak detection and performance analysis. The skill identifies potential issues such as unremoved event listeners, closures preventing garbage collection, uncancelled timers, unbounded cache growth, circular references, detached DOM nodes, and unnecessary global state accumulation. It then provides detailed fix recommendations. Use this skill to proactively identify and resolve memory leaks, improving application performance and stability.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill helps you identify and resolve memory leaks in your code. By analyzing your code for common memory leak patterns, it can help you improve the performance and stability of your application.

## How It Works

1. **Initiate Analysis**: The user requests memory leak detection.
2. **Code Analysis**: The plugin analyzes the codebase for potential memory leak patterns.
3. **Report Generation**: The plugin generates a report detailing potential memory leaks and recommended fixes.

## When to Use This Skill

This skill activates when you need to:
- Detect potential memory leaks in your application.
- Analyze memory usage patterns to identify performance bottlenecks.
- Troubleshoot performance issues related to memory leaks.

## Examples

### Example 1: Identifying Event Listener Leaks

User request: "detect memory leaks in my event handling code"

The skill will:
1. Analyze the code for unremoved event listeners.
2. Generate a report highlighting potential event listener leaks and suggesting how to properly remove them.

### Example 2: Analyzing Cache Growth

User request: "analyze memory usage to find excessive cache growth"

The skill will:
1. Analyze cache implementations for unbounded growth.
2. Identify caches that are not properly managed and recommend strategies for limiting their size.

## Best Practices

- **Code Review**: Always review the reported potential leaks to ensure they are genuine issues.
- **Regular Analysis**: Incorporate memory leak detection into your regular development workflow.
- **Targeted Analysis**: Focus your analysis on specific areas of your code that are known to be memory-intensive.

## Integration

This skill can be used in conjunction with other performance analysis tools to provide a comprehensive view of application performance.