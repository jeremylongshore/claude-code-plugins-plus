---
name: vercel-rate-limits
description: |
  Implement Vercel rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Vercel.
  Trigger with phrases like "vercel rate limit", "vercel throttling",
  "vercel 429", "vercel retry", "vercel backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Rate Limits

## Prerequisites
- Vercel SDK installed
- Understanding of async/await patterns
- Access to rate limit headers


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Reliable API calls with automatic retry
- Idempotent requests preventing duplicates
- Rate limit headers properly handled

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Rate Limits](https://vercel.com/docs/rate-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Overview

Implement Vercel rate limiting, backoff, and idempotency patterns.

## Instructions

1. Assess the current state of the API configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference