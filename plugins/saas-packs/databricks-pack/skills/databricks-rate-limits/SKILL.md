---
name: databricks-rate-limits
description: |
  Implement Databricks API rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Databricks.
  Trigger with phrases like "databricks rate limit", "databricks throttling",
  "databricks 429", "databricks retry", "databricks backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Rate Limits

## Overview
Handle Databricks API rate limits gracefully with exponential backoff.

## Prerequisites
- Databricks SDK installed
- Understanding of async/await patterns
- Access to Databricks workspace

## Instructions

### Step 1: Understand Rate Limit Tiers

### Step 2: Implement Exponential Backoff with Jitter

### Step 3: Implement Request Queue for Bulk Operations

### Step 4: Async Batch Processing

### Step 5: Idempotency for Job Submissions

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Reliable API calls with automatic retry
- Rate-limited request queue
- Async batch processing for bulk operations
- Idempotent job submissions

## Error Handling
| Scenario | Behavior | Configuration |
|----------|----------|---------------|
| HTTP 429 | Exponential backoff | `max_retries=5` |
| HTTP 503 | Retry with delay | `base_delay=1.0` |
| Conflict (409) | Retry once | Check idempotency |
| Timeout | Retry with increased timeout | `max_delay=60` |

## Resources
- [Databricks API Rate Limits](https://docs.databricks.com/dev-tools/api/latest/rate-limits.html)
- [Best Practices for API Usage](https://docs.databricks.com/dev-tools/api/latest/best-practices.html)

## Next Steps
For security configuration, see `databricks-security-basics`.

## Examples

**Basic usage**: Apply databricks rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize databricks rate limits for production environments with multiple constraints and team-specific requirements.