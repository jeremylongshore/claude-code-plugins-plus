---
name: customerio-reliability-patterns
description: |
  Implement Customer.io reliability patterns.
  Use when building fault-tolerant integrations,
  implementing circuit breakers, or handling failures.
  Trigger with phrases like "customer.io reliability", "customer.io resilience",
  "customer.io circuit breaker", "customer.io fault tolerance".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Reliability Patterns

## Overview
Implement reliability patterns for fault-tolerant Customer.io integrations including circuit breakers, retries with jitter, fallback queues, and idempotency.

## Prerequisites
- Customer.io integration working
- Understanding of failure modes
- Queue infrastructure (optional)

## Instructions

### Step 1: Implement Circuit Breaker
Build a circuit breaker with CLOSED/OPEN/HALF_OPEN states, configurable failure/success thresholds, and automatic recovery timeout.

### Step 2: Add Retry with Jitter
Create exponential backoff with configurable jitter (0-30%) to prevent thundering herd. Skip retries on client errors (4xx except 429).

### Step 3: Set Up Fallback Queue
Use BullMQ to queue operations when the circuit breaker is open, with exponential backoff retries starting at 1 minute.

### Step 4: Build Graceful Degradation Layer
Wrap the Customer.io client with circuit breaker and fallback queue integration for automatic failover.

### Step 5: Add Health Checks
Create a health check endpoint that tests API connectivity, reports circuit state, queue depth, and last success/failure times.

### Step 6: Implement Idempotency
Use SHA-256 content hashing with LRU cache to prevent duplicate operations within a configurable window.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Pattern | When to Use |
|---------|-------------|
| Circuit Breaker | Prevent cascade failures |
| Retry | Transient errors (5xx, 429) |
| Fallback Queue | Extended outages |
| Idempotency | Duplicate prevention |

## Reliability Checklist
- [ ] Circuit breaker implemented
- [ ] Retry with exponential backoff
- [ ] Fallback queue for failures
- [ ] Health check endpoint
- [ ] Idempotency for duplicates
- [ ] Timeout configuration
- [ ] Graceful shutdown handling

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Retry Best Practices](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

## Next Steps
After reliability patterns, proceed to `customerio-load-scale` for scaling.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Customerio Reliability Patterns implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply customerio reliability patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio reliability patterns for production environments with multiple constraints and team-specific requirements.