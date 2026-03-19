---
name: guidewire-debug-bundle
description: |
  Debug Guidewire InsuranceSuite issues including Gosu code, Cloud API integrations,
  and system performance problems.
  Use when troubleshooting errors, analyzing logs, or diagnosing integration failures.
  Trigger with phrases like "debug guidewire", "troubleshoot policycenter",
  "gosu debugging", "guidewire logs", "trace api call".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(grep:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

Comprehensive debugging techniques for Guidewire InsuranceSuite including Gosu debugging, Cloud API tracing, log analysis, and performance profiling.

## Prerequisites

- Access to Guidewire Cloud Console
- IntelliJ IDEA with Gosu plugin
- Basic understanding of Java debugging
- Access to application logs

## Instructions

### Step 1: Enable Debug Logging

Configure Log4j2 with DEBUG level for `gw.custom`, `gw.plugin`, `gw.api.rest`, `gw.api.database`, and `gw.integration` categories. Use rolling file appender with 100 MB size limit.

### Step 2: Gosu Debugging in IDE

Use the `DebugHelper` class for method tracing, entity state dumps, and query profiling. Set breakpoints in IntelliJ and attach to the debug port (5005).

### Step 3: Remote Debugging Setup

```bash
export JAVA_OPTS="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005"  # 5005 = configured value
./gradlew runServer
```

In IntelliJ: Run > Edit Configurations > Remote JVM Debug (localhost:5005).

### Step 4: API Request Tracing

Add axios interceptors to log request/response details with unique request IDs and Guidewire trace IDs (`x-gw-trace-id`).

### Step 5: Cloud Console Log Analysis

Use Lucene queries in Guidewire Cloud Console Observability > Logs to search for errors by claim number, slow API calls, auth failures, or integration errors.

### Step 6: Database Query Analysis

Profile queries with `QueryPlanExplainer` to detect full table scans and slow queries exceeding 1 second.

### Step 7: Memory and Thread Analysis

Monitor JVM memory usage and dump thread state when investigating performance issues or deadlocks.

For detailed code implementations (Log4j2 config, Gosu helpers, TypeScript tracing, query analysis), load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Debug logs with trace information
- Query execution plans
- Memory and thread dumps
- Complete debug bundle for support

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| No debug logs | Wrong log level | Set categories to DEBUG |
| Debugger won't attach | Wrong port or firewall | Verify JAVA_OPTS and port |
| Slow query undetected | No profiling | Wrap queries with profileQuery |
| Missing trace IDs | Headers not logged | Add response interceptor |

## Resources

- [Guidewire Cloud Console](https://gcc.guidewire.com/)
- [IntelliJ Debugging Guide](https://www.jetbrains.com/help/idea/debugging-code.html)
- [Log4j2 Configuration](https://logging.apache.org/log4j/2.x/manual/configuration.html)

## Next Steps

For rate limiting information, see `guidewire-rate-limits`.

## Examples

**Basic usage**: Apply guidewire debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire debug bundle for production environments with multiple constraints and team-specific requirements.