---
name: analyzing-logs
description: Analyze application logs for performance insights and issue detection including slow requests, error patterns, and resource usage. Use when troubleshooting performance issues or debugging errors. Trigger with phrases like "analyze logs", "find slow requests", or "detect error patterns".
version: 1.0.0
allowed-tools: "Read, Write, Bash(logs:*), Bash(grep:*), Bash(awk:*), Grep"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Log Analysis Tool

This skill provides automated assistance for log analysis tool tasks.

## Overview

This skill empowers Claude to automatically analyze application logs, pinpoint performance bottlenecks, and identify recurring errors. It streamlines the debugging process and helps optimize application performance by extracting key insights from log data.

## How It Works

1. **Initiate Analysis**: Claude activates the log analysis tool upon detecting relevant trigger phrases.
2. **Log Data Extraction**: The tool extracts relevant data, including timestamps, request durations, error messages, and resource usage metrics.
3. **Pattern Identification**: The tool identifies patterns such as slow requests, frequent errors, and resource exhaustion warnings.
4. **Report Generation**: Claude presents a summary of findings, highlighting potential performance issues and optimization opportunities.

## When to Use This Skill

This skill activates when you need to:
- Identify performance bottlenecks in an application.
- Debug recurring errors and exceptions.
- Analyze log data for trends and anomalies.
- Set up structured logging or log aggregation.

## Examples

### Example 1: Identifying Slow Requests

User request: "Analyze logs for slow requests."

The skill will:
1. Activate the log analysis tool.
2. Identify requests exceeding predefined latency thresholds.
3. Present a list of slow requests with corresponding timestamps and durations.

### Example 2: Detecting Error Patterns

User request: "Find error patterns in the application logs."

The skill will:
1. Activate the log analysis tool.
2. Scan logs for recurring error messages and exceptions.
3. Group similar errors and present a summary of error frequencies.

## Best Practices

- **Log Level**: Ensure appropriate log levels (e.g., INFO, WARN, ERROR) are used to capture relevant information.
- **Structured Logging**: Implement structured logging (e.g., JSON format) to facilitate efficient analysis.
- **Log Rotation**: Configure log rotation policies to prevent log files from growing excessively.

## Integration

This skill can be integrated with other tools for monitoring and alerting. For example, it can be used in conjunction with a monitoring plugin to automatically trigger alerts based on log analysis results. It can also work with deployment tools to rollback deployments when critical errors are detected in the logs.

## Prerequisites

- Access to application log files in {baseDir}/logs/
- Log parsing tools (grep, awk, sed)
- Understanding of application log format and structure
- Read permissions for log directories

## Instructions

1. Identify log files to analyze based on timeframe and application
2. Extract relevant data (timestamps, durations, error messages)
3. Apply pattern matching to identify slow requests and errors
4. Aggregate and group similar issues
5. Generate analysis report with findings and recommendations
6. Suggest optimization opportunities based on patterns

## Output

- Summary of slow requests with response times
- Error frequency reports grouped by type
- Resource usage patterns and anomalies
- Performance bottleneck identification
- Recommendations for log improvements and optimizations

## Error Handling

If log analysis fails:
- Verify log file paths and permissions
- Check log format compatibility
- Validate timestamp parsing
- Ensure sufficient disk space for analysis
- Review log rotation configuration

## Resources

- Application logging best practices
- Structured logging format guides
- Log aggregation tools documentation
- Performance analysis methodologies