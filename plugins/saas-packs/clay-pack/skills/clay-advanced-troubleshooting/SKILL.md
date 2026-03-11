---
name: clay-advanced-troubleshooting
description: |
  Apply Clay advanced debugging techniques for hard-to-diagnose issues.
  Use when standard troubleshooting fails, investigating complex race conditions,
  or preparing evidence bundles for Clay support escalation.
  Trigger with phrases like "clay hard bug", "clay mystery error",
  "clay impossible to debug", "difficult clay issue", "clay deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Advanced Troubleshooting

## Overview

Deep debugging techniques for complex Clay issues that resist standard troubleshooting.

## Prerequisites

- Access to production logs and metrics
- kubectl access to clusters
- Network capture tools available
- Understanding of distributed tracing

## Instructions

### Step 1: Collect Evidence Bundle

Run the comprehensive debug script to gather pod logs, Prometheus metrics, network captures, Jaeger traces, and configuration state into a timestamped tarball.

### Step 2: Systematic Layer Isolation

Test each layer independently: network connectivity, DNS resolution, TLS handshake, authentication, API response, and response parsing. The first failure identifies the root cause layer.

### Step 3: Create Minimal Reproduction

Strip down to the simplest failing case: fresh client, no customization, simplest API call (ping). Log full error details including stack trace.

### Step 4: Timing and Resource Analysis

Use `TimingAnalyzer` to measure each operation and detect latency anomalies. Monitor heap usage over time to detect memory leaks (>100MB growth over 1 hour). Use `ConcurrencyChecker` to detect race conditions.

### Step 5: Escalate with Evidence

Fill out the support escalation template with severity, request ID, reproduction steps, expected vs actual behavior, and attach all collected evidence.

For complete debug scripts, TypeScript utilities, and escalation template, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Comprehensive debug bundle collected
- Failure layer identified
- Minimal reproduction created
- Support escalation submitted

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reproduce | Race condition | Add timing analysis |
| Intermittent failure | Timing-dependent | Increase sample size |
| No useful logs | Missing instrumentation | Add debug logging |
| Memory growth | Resource leak | Use heap profiling |

## Resources

- [Clay Support Portal](https://support.clay.com)
- [Clay Status Page](https://status.clay.com)

## Next Steps

For load testing, see `clay-load-scale`.

## Examples

**Basic usage**: Apply clay advanced troubleshooting to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay advanced troubleshooting for production environments with multiple constraints and team-specific requirements.