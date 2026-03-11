---
name: clay-reliability-patterns
description: |
  Implement Clay reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Clay integrations, implementing retry strategies,
  or adding resilience to production Clay services.
  Trigger with phrases like "clay reliability", "clay circuit breaker",
  "clay idempotent", "clay resilience", "clay fallback", "clay bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Reliability Patterns

## Overview

Production reliability patterns for Clay data enrichment pipelines. Clay's async enrichment model, credit-based billing, and multi-provider waterfall architecture require specific resilience strategies.

## Prerequisites

- Clay API access configured
- Understanding of Clay's async enrichment model
- Queue infrastructure (Redis) for retry handling

## Instructions

### Step 1: Implement Enrichment Job Tracking

Track submitted jobs in Redis with table ID, row count, submission time, and status. Detect stuck enrichments by checking elapsed time against a 30-minute timeout.

### Step 2: Add Credit Budget Circuit Breaker

Track daily credit usage in Redis. Before each batch, check if estimated credits would exceed the daily limit. Stop processing when budget is exhausted to prevent runaway costs.

### Step 3: Monitor Provider Health

Track success/failure rates per enrichment provider over a sliding window of 100 requests. Filter out providers below 50% success rate from waterfall configurations.

### Step 4: Use Dead Letter Queue for Failed Batches

Process rows in batches of 50 with 2-second delays. On failure, push the batch to a DLQ for manual review instead of blocking the pipeline.

For complete Python implementations with Redis-backed tracking, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Runaway credit spend | No budget limit | Implement credit circuit breaker |
| Stuck enrichments | Async job not completing | Track jobs with timeout detection |
| Provider degradation | Upstream data source down | Monitor provider success rates |
| Batch failures | API errors mid-batch | DLQ for failed rows, retry later |

## Resources

- [Clay API Reference](https://docs.clay.com/api)
- [Enrichment Best Practices](https://docs.clay.com/best-practices)
