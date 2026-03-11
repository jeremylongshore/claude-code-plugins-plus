---
name: juicebox-rate-limits
description: |
  Implement Juicebox rate limiting and backoff.
  Use when handling API quotas, implementing retry logic,
  or optimizing request throughput.
  Trigger with phrases like "juicebox rate limit", "juicebox quota",
  "juicebox throttling", "juicebox backoff".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Rate Limits

## Overview
Understand and implement proper rate limiting handling for Juicebox API.

## Instructions
1. Step 1: Understand Rate Limit Headers
2. Step 2: Implement Rate Limiter
3. Step 3: Add Exponential Backoff
4. Step 4: Implement Quota Tracking

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Rate limiter with queue
- Exponential backoff handler
- Quota tracking system
- Header parsing utilities

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 with Retry-After | Wait exact duration |
| 429 without Retry-After | Exponential backoff |
| Approaching limit | Proactive throttling |
| Daily quota exhausted | Queue for next day |

## Resources
- [Rate Limits Documentation](https://juicebox.ai/docs/rate-limits)
- [Quota Dashboard](https://app.juicebox.ai/usage)

## Next Steps
After rate limit handling, see `juicebox-security-basics` for security best practices.

## Prerequisites

- Access to the API environment or API
- Required CLI tools installed and authenticated
- Familiarity with API concepts and terminology

## Examples

**Basic usage**: Apply juicebox rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox rate limits for production environments with multiple constraints and team-specific requirements.