---
name: customerio-performance-tuning
description: |
  Optimize Customer.io API performance.
  Use when improving response times, reducing latency,
  or optimizing high-volume integrations.
  Trigger with phrases like "customer.io performance", "optimize customer.io",
  "customer.io latency", "customer.io speed".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Performance Tuning

## Overview
Optimize Customer.io API performance for high-volume and low-latency integrations through connection pooling, batching, caching, and regional routing.

## Prerequisites
- Customer.io integration working
- Monitoring infrastructure
- Understanding of your traffic patterns

## Instructions

### Step 1: Enable Connection Pooling
Create an HTTPS agent with keep-alive, configure max sockets, and use a singleton client pattern for connection reuse.

### Step 2: Implement Batch Processing
Build a batch processor that collects operations, flushes on size threshold or time interval, and processes with controlled concurrency.

### Step 3: Add Async Fire-and-Forget
Create a non-blocking tracker with internal queue processing for events that don't need synchronous confirmation.

### Step 4: Set Up Deduplication Cache
Use LRU caches to skip duplicate identify calls within a TTL window and deduplicate events by event ID or composite key.

### Step 5: Configure Regional Routing
Route API calls to the nearest Customer.io region (US/EU) based on user preferences or geolocation.

### Step 6: Add Performance Monitoring
Wrap all Customer.io operations with timing metrics to track latency, success rates, and error rates.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Performance Benchmarks
| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Identify | < 100ms | With connection pooling |
| Track Event | < 100ms | With connection pooling |
| Batch (100 items) | < 500ms | Parallel processing |
| Webhook Processing | < 50ms | Excluding downstream ops |

## Error Handling
| Issue | Solution |
|-------|----------|
| High latency | Enable connection pooling |
| Timeout errors | Reduce payload size, increase timeout |
| Memory pressure | Limit cache and queue sizes |

## Resources
- [API Performance Tips](https://customer.io/docs/api/track/#section/Rate-limits)
- [Best Practices](https://customer.io/docs/best-practices/)

## Next Steps
After performance tuning, proceed to `customerio-cost-tuning` for cost optimization.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply customerio performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio performance tuning for production environments with multiple constraints and team-specific requirements.