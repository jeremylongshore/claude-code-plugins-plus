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
1. Step 1: Query Optimization
2. Step 2: Implement Caching Layer
3. Step 3: Cached Client Wrapper
4. Step 4: Request Batching
5. Step 5: Connection Pooling
6. Step 6: Query Complexity Monitoring

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Linear GraphQL Best Practices](https://developers.linear.app/docs/graphql/best-practices)
- [Query Complexity](https://developers.linear.app/docs/graphql/complexity)
- [Redis Caching Guide](https://redis.io/docs/manual/patterns/)

## Next Steps
Optimize costs with `linear-cost-tuning`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with ORM |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply linear performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear performance tuning for production environments with multiple constraints and team-specific requirements.