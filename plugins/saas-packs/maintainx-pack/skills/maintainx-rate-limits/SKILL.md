---
name: maintainx-rate-limits
description: |
  Implement MaintainX API rate limiting, pagination, and backoff patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for MaintainX.
  Trigger with phrases like "maintainx rate limit", "maintainx throttling",
  "maintainx 429", "maintainx retry", "maintainx backoff", "maintainx pagination".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Rate Limits

## Overview
Handle MaintainX API rate limits gracefully with exponential backoff, pagination, and request queuing.

## Prerequisites
- MaintainX SDK installed
- Understanding of async/await patterns
- Familiarity with cursor-based pagination

## Instructions
Follow these high-level steps to implement maintainx-rate-limits:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-rate-limits/references/implementation-guide.md)`

## Output
- Resilient API calls with automatic retry
- Proper pagination handling
- Request queuing and throttling
- Rate limit monitoring

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 Rate Limited | Exponential backoff with jitter |
| Retry-After header | Honor the specified wait time |
| Burst requests | Use request queue |
| Large data sets | Use pagination with delays |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Rate Limiting Best Practices](https://www.merge.dev/blog/api-rate-limit-best-practices)

## Next Steps
For security configuration, see `maintainx-security-basics`.
