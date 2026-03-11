---
name: linear-rate-limits
description: |
  Handle Linear API rate limiting and quotas effectively.
  Use when dealing with rate limit errors, implementing throttling,
  or optimizing API usage patterns.
  Trigger with phrases like "linear rate limit", "linear throttling",
  "linear API quota", "linear 429 error", "linear request limits".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Rate Limits

## Overview
Understand and handle Linear API rate limits for reliable integrations.

## Prerequisites
- Linear SDK configured
- Understanding of HTTP headers
- Familiarity with async patterns

## Instructions
- Step 1: Basic Rate Limit Handler
- Step 2: Exponential Backoff
- Step 3: Request Queue
- Step 4: Batch Operations
- Step 5: Query Optimization

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Rate limit monitoring
- Automatic retry with backoff
- Request queuing and throttling
- Batch processing utilities
- Optimized query patterns

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Use backoff and queue |
| `Complexity exceeded` | Query too expensive | Simplify query structure |
| `Timeout` | Long-running query | Paginate or split queries |

## Resources
- [Linear Rate Limiting](https://developers.linear.app/docs/graphql/rate-limiting)
- [GraphQL Complexity](https://developers.linear.app/docs/graphql/complexity)
- [Best Practices](https://developers.linear.app/docs/graphql/best-practices)

## Next Steps
Learn security best practices with `linear-security-basics`.
