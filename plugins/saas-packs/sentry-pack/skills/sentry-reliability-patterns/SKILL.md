---
name: sentry-reliability-patterns
description: |
  Build reliable Sentry integrations.
  Use when handling SDK failures gracefully,
  implementing retry logic, or ensuring error tracking uptime.
  Trigger with phrases like "sentry reliability", "sentry failover",
  "sentry sdk failure handling", "resilient sentry setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Reliability Patterns

## Prerequisites

- Understanding of failure modes
- Fallback logging strategy
- Network reliability characteristics
- Graceful shutdown requirements

## Instructions

1. Wrap Sentry.init with try/catch for graceful initialization failure handling
2. Implement fallback capture function that logs locally if Sentry fails
3. Add retry with exponential backoff for network failures
4. Implement offline event queue for intermittent connectivity
5. Add circuit breaker pattern to skip Sentry after repeated failures
6. Configure request timeout with wrapper function
7. Implement graceful shutdown with Sentry.close() on SIGTERM
8. Set up dual-write pattern to multiple error trackers for redundancy
9. Create health check endpoint to verify Sentry connectivity
10. Test all failure scenarios to ensure application continues operating

## Output
- Graceful degradation implemented
- Circuit breaker pattern applied
- Offline queue configured
- Dual-write reliability enabled

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Configuration](https://docs.sentry.io/platforms/javascript/configuration/)
- [Transport Options](https://docs.sentry.io/platforms/javascript/configuration/transports/)

## Overview

Build reliable Sentry integrations.