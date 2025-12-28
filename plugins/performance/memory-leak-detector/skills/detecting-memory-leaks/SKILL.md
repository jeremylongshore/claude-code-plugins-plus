---
name: detecting-memory-leaks
description: Detect potential memory leaks and analyze memory usage patterns in code. Use when troubleshooting performance issues related to memory growth or identifying leak sources. Trigger with phrases like "detect memory leaks", "analyze memory usage", or "find memory issues".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(profiling:*), Bash(memory:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Memory Leak Detector

This skill provides automated assistance for memory leak detector tasks.

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

## Prerequisites

- Access to application source code in {baseDir}/
- Memory profiling tools (valgrind, heapdump, etc.)
- Understanding of application memory architecture
- Runtime environment for testing

## Instructions

1. Analyze code for common memory leak patterns
2. Identify unremoved event listeners and callbacks
3. Check for unbounded cache growth
4. Review closure usage and retained references
5. Generate report with leak locations and severity
6. Provide remediation recommendations

## Output

- Memory leak detection report with file locations
- Pattern analysis for event listeners and caches
- Memory usage trends and growth patterns
- Code snippets highlighting potential leaks
- Recommended fixes with code examples

## Error Handling

If memory leak detection fails:
- Verify code file access permissions
- Check profiling tool installation
- Validate code syntax and structure
- Ensure sufficient memory for analysis
- Review runtime environment configuration

## Resources

- Memory profiling tool documentation
- Memory leak detection best practices
- JavaScript/Node.js memory management guides
- Performance optimization resources