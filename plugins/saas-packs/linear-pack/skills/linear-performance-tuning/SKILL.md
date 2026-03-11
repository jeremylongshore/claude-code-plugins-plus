---
name: linear-performance-tuning
description: |
  Optimize Linear API queries and caching for better performance.
  Use when improving response times, reducing API calls,
  or implementing caching strategies.
  Trigger with phrases like "linear performance", "optimize linear",
  "linear caching", "linear slow queries", "speed up linear".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Performance Tuning

## Overview
Optimize Linear API usage for maximum performance and minimal latency.

## Prerequisites
- Working Linear integration
- Understanding of GraphQL
- Caching infrastructure (Redis recommended)

## Instructions
- Step 1: Query Optimization
- Step 2: Implement Caching Layer
- Step 3: Cached Client Wrapper
- Step 4: Request Batching
- Step 5: Connection Pooling
- Step 6: Query Complexity Monitoring

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Linear GraphQL Best Practices](https://developers.linear.app/docs/graphql/best-practices)
- [Query Complexity](https://developers.linear.app/docs/graphql/complexity)
- [Redis Caching Guide](https://redis.io/docs/manual/patterns/)

## Next Steps
Optimize costs with `linear-cost-tuning`.
