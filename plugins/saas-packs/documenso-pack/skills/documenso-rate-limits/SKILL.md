---
name: documenso-rate-limits
description: |
  Implement Documenso rate limiting, backoff, and request throttling patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Documenso.
  Trigger with phrases like "documenso rate limit", "documenso throttling",
  "documenso 429", "documenso retry", "documenso backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Rate Limits

## Overview
Handle Documenso API rate limits gracefully with exponential backoff, request queuing, and fair use compliance.

## Prerequisites
- Documenso SDK installed
- Understanding of async/await patterns
- Queue library (optional but recommended)

## Instructions

### Step 1: Documenso Fair Use Policy
Documenso implements fair use rate limiting. While specific limits are not publicly documented, follow these guidelines:
### Step 2: Instructions
interface BackoffConfig {

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Documenso Fair Use Policy
- Instructions

## Error Handling
| Scenario | Response | Action |
|----------|----------|--------|
| 429 Rate Limited | Wait and retry | Use exponential backoff |
| Retry-After header | Honor the value | Wait specified seconds |
| Persistent 429 | Queue full | Reduce concurrency |
| 503 Service Unavailable | Temporary | Retry with longer delay |

## Resources
- [Documenso Fair Use Policy](https://docs.documenso.com/developers/public-api)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Retry Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)

## Next Steps
For security configuration, see `documenso-security-basics`.

## Examples

**Basic usage**: Apply documenso rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso rate limits for production environments with multiple constraints and team-specific requirements.