---
name: lokalise-rate-limits
description: |
  Implement Lokalise rate limiting, backoff, and request queuing patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Lokalise.
  Trigger with phrases like "lokalise rate limit", "lokalise throttling",
  "lokalise 429", "lokalise retry", "lokalise backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Rate Limits

## Overview
Handle Lokalise rate limits gracefully with request queuing, exponential backoff, and monitoring.

## Prerequisites
- Lokalise SDK installed
- Understanding of async/await patterns
- Access to rate limit headers

## Instructions
1. **Rate Limit Specifications**
2. **Instructions**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Request queue respecting 6 req/sec limit
- Automatic retry with exponential backoff
- Proactive throttling when quota low
- Batch processing for large operations

## Error Handling
| Header | Description | Action |
|--------|-------------|--------|
| X-RateLimit-Limit | Max requests per window | Monitor usage |
| X-RateLimit-Remaining | Remaining requests | Throttle if low |
| X-RateLimit-Reset | Unix timestamp of reset | Wait until reset |
| Retry-After | Seconds to wait (on 429) | Honor this value |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Lokalise Rate Limits](https://developers.lokalise.com/reference/api-rate-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `lokalise-security-basics`.
