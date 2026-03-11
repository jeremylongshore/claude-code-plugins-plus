---
name: apollo-rate-limits
description: |
  Implement Apollo.io rate limiting and backoff.
  Use when handling rate limits, implementing retry logic,
  or optimizing API request throughput.
  Trigger with phrases like "apollo rate limit", "apollo 429",
  "apollo throttling", "apollo backoff", "apollo request limits".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Rate Limits

## Overview
Implement robust rate limiting and backoff strategies for Apollo.io API to maximize throughput while avoiding 429 errors.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-rate-limits:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-rate-limits/references/implementation-guide.md)`

## Output
- Rate limiter class with token bucket algorithm
- Exponential backoff with jitter
- Request queue with concurrency control
- Priority-based request scheduling
- Rate limit monitoring and alerts

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 response | Use Retry-After header |
| Burst limit hit | Add minimum spacing |
| Sustained limit | Queue with concurrency |
| Network timeout | Exponential backoff |

## Resources
- [Apollo Rate Limits](https://apolloio.github.io/apollo-api-docs/#rate-limits)
- [p-queue Library](https://github.com/sindresorhus/p-queue)
- [Exponential Backoff](https://cloud.google.com/storage/docs/exponential-backoff)

## Next Steps
Proceed to `apollo-security-basics` for API security best practices.
