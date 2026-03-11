---
name: vercel-reliability-patterns
description: |
  Implement Vercel reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Vercel integrations, implementing retry strategies,
  or adding resilience to production Vercel services.
  Trigger with phrases like "vercel reliability", "vercel circuit breaker",
  "vercel idempotent", "vercel resilience", "vercel fallback", "vercel bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Reliability Patterns

## Prerequisites
- Understanding of circuit breaker pattern
- opossum or similar library installed
- Queue infrastructure for DLQ
- Caching layer for fallbacks

## Instructions

### Step 1: Implement Circuit Breaker
Wrap Vercel calls with circuit breaker.

### Step 2: Add Idempotency Keys
Generate deterministic keys for operations.

### Step 3: Configure Bulkheads
Separate queues for different priorities.

### Step 4: Set Up Dead Letter Queue
Handle permanent failures gracefully.

## Output
- Circuit breaker protecting Vercel calls
- Idempotency preventing duplicates
- Bulkhead isolation implemented
- DLQ for failed operations

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Documentation](https://nodeshift.dev/opossum/)
- [Vercel Reliability Guide](https://vercel.com/docs/reliability)

## Overview

Implement Vercel reliability patterns including circuit breakers, idempotency, and graceful degradation.