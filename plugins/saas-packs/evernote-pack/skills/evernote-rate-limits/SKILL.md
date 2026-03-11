---
name: evernote-rate-limits
description: |
  Handle Evernote API rate limits effectively.
  Use when implementing rate limit handling, optimizing API usage,
  or troubleshooting rate limit errors.
  Trigger with phrases like "evernote rate limit", "evernote throttling",
  "api quota evernote", "rate limit exceeded".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Rate Limits

## Overview
Evernote enforces rate limits per API key, per user, per hour. Understanding and handling these limits is essential for production integrations.

## Prerequisites
- Evernote SDK setup
- Understanding of async/await patterns
- Error handling implementation

## Instructions

### Step 1: Rate Limit Handler

### Step 2: Rate-Limited Client Wrapper

### Step 3: Batch Operations with Rate Limiting

### Step 4: Avoiding Rate Limits

### Step 5: Rate Limit Monitoring

### Step 6: Usage Example

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Automatic retry with exponential backoff
- Request queuing to prevent bursts
- Batch processing with progress tracking
- Rate limit monitoring and statistics
- Optimized API usage patterns

## Error Handling
| Scenario | Response |
|----------|----------|
| First rate limit | Wait rateLimitDuration, retry |
| Repeated rate limits | Increase base delay, reduce batch size |
| Rate limit + other error | Handle other error first |
| Rate limit on initial sync | Request rate limit boost |

## Resources
- [Rate Limits Overview](https://dev.evernote.com/doc/articles/rate_limits.php)
- [Best Practices](https://dev.evernote.com/doc/articles/rate_limits_best_practices.php)
- [Webhooks](https://dev.evernote.com/doc/articles/webhooks.php)

## Next Steps
For security considerations, see `evernote-security-basics`.

## Examples

**Basic usage**: Apply evernote rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote rate limits for production environments with multiple constraints and team-specific requirements.