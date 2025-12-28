---
name: analyzing-network-latency
description: Analyze network latency and optimize request patterns for faster communication. Use when diagnosing slow network performance or optimizing API calls. Trigger with phrases like "analyze network latency", "optimize API calls", or "reduce network delays".
version: 1.0.0
allowed-tools: "Read, Write, Bash(curl:*), Bash(ping:*), Bash(traceroute:*), Grep"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Network Latency Analyzer

This skill provides automated assistance for network latency analyzer tasks.

## Overview

This skill empowers Claude to diagnose network latency issues and propose optimizations to improve application performance. It analyzes request patterns, identifies potential bottlenecks, and recommends solutions for faster and more efficient network communication.

## How It Works

1. **Request Pattern Identification**: Claude identifies all network requests made by the application.
2. **Latency Analysis**: Claude analyzes the latency associated with each request, looking for patterns and anomalies.
3. **Optimization Recommendations**: Claude suggests optimizations such as parallelization, request batching, connection pooling, and timeout adjustments.

## When to Use This Skill

This skill activates when you need to:
- Analyze network latency in an application.
- Optimize network request patterns for improved performance.
- Identify bottlenecks in network communication.

## Examples

### Example 1: Optimizing API Calls

User request: "Analyze network latency and suggest improvements for our API calls."

The skill will:
1. Identify all API calls made by the application.
2. Analyze the latency of each API call.
3. Suggest parallelizing certain API calls and implementing connection pooling.

### Example 2: Reducing Page Load Time

User request: "Optimize network request patterns to reduce page load time."

The skill will:
1. Identify all network requests made during page load.
2. Analyze the latency of each request.
3. Suggest batching multiple requests into a single request and optimizing timeout configurations.

## Best Practices

- **Parallelization**: Identify serial requests that can be executed in parallel to reduce overall latency.
- **Request Batching**: Batch multiple small requests into a single larger request to reduce overhead.
- **Connection Pooling**: Reuse existing HTTP connections to avoid the overhead of establishing new connections for each request.

## Integration

This skill can be used in conjunction with other plugins that manage infrastructure or application code, allowing for automated implementation of the suggested optimizations. For instance, it can work with a code modification plugin to automatically apply connection pooling or adjust timeout values.

## Prerequisites

- Access to application network configuration
- Network monitoring tools (curl, ping, traceroute)
- Request pattern documentation
- Performance baseline metrics

## Instructions

1. Identify all network requests in the application
2. Measure latency for each request type
3. Analyze patterns for serial vs parallel execution
4. Identify opportunities for batching and pooling
5. Recommend timeout and retry configurations
6. Provide optimization implementation plan

## Output

- Network latency analysis report
- Request pattern visualizations
- Optimization recommendations with priorities
- Implementation examples for suggested changes
- Expected performance improvements

## Error Handling

If latency analysis fails:
- Verify network connectivity to endpoints
- Check DNS resolution and routing
- Validate request authentication
- Review firewall and security rules
- Ensure monitoring tools are installed

## Resources

- HTTP connection pooling guides
- Request batching best practices
- Network performance optimization references
- API design patterns for latency reduction