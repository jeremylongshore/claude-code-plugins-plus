---
name: clerk-rate-limits
description: |
  Understand and manage Clerk rate limits and quotas.
  Use when hitting rate limits, optimizing API usage,
  or planning for high-traffic scenarios.
  Trigger with phrases like "clerk rate limit", "clerk quota",
  "clerk API limits", "clerk throttling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Rate Limits

## Overview
Understand Clerk's rate limiting system and implement strategies to avoid hitting limits.

## Prerequisites
- Clerk account with API access
- Understanding of your application's traffic patterns
- Monitoring/logging infrastructure

## Instructions
1. Step 1: Understand Rate Limits
2. Step 2: Implement Rate Limit Handling
3. Step 3: Batch Operations
4. Step 4: Caching Strategy
5. Step 5: Monitor Rate Limit Usage

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Rate limit handling with retries
- Batched API operations
- Caching implementation
- Monitoring system

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 429 Too Many Requests | Rate limit exceeded | Implement backoff, cache more |
| quota_exceeded | Monthly quota hit | Upgrade plan or reduce usage |
| concurrent_limit | Too many parallel requests | Queue requests |

## Resources
- [Clerk Rate Limits](https://clerk.com/docs/backend-requests/resources/rate-limits)
- [API Best Practices](https://clerk.com/docs/backend-requests/overview)
- [Pricing & Quotas](https://clerk.com/pricing)

## Next Steps
Proceed to `clerk-security-basics` for security best practices.

## Examples

**Basic usage**: Apply clerk rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk rate limits for production environments with multiple constraints and team-specific requirements.