---
name: supabase-reliability-patterns
description: |
  Implement Supabase reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Supabase integrations, implementing retry strategies,
  or adding resilience to production Supabase services.
  Trigger with phrases like "supabase reliability", "supabase circuit breaker",
  "supabase idempotent", "supabase resilience", "supabase fallback", "supabase bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Reliability Patterns

## Prerequisites
- Understanding of circuit breaker pattern
- opossum or similar library installed
- Queue infrastructure for DLQ
- Caching layer for fallbacks

## Instructions

### Step 1: Implement Circuit Breaker
Wrap Supabase calls with circuit breaker.

### Step 2: Add Idempotency Keys
Generate deterministic keys for operations.

### Step 3: Configure Bulkheads
Separate queues for different priorities.

### Step 4: Set Up Dead Letter Queue
Handle permanent failures gracefully.

## Output
- Circuit breaker protecting Supabase calls
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
- [Supabase Reliability Guide](https://supabase.com/docs/reliability)
