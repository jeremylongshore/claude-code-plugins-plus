---
name: lindy-rate-limits
description: |
  Manage and optimize Lindy AI rate limits.
  Use when hitting rate limits, optimizing API usage,
  or implementing rate limit handling.
  Trigger with phrases like "lindy rate limit", "lindy quota",
  "lindy throttling", "lindy API limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Rate Limits

## Overview
Rate limit management for Lindy AI agent API. Lindy's agent execution model involves orchestrating multiple service calls per request, making rate limits apply at both the API level and the agent action level.

## Prerequisites
- Lindy API configured
- Understanding of agent execution costs
- Monitoring for action-level limits

## Lindy Rate Limits

| Resource | Limit | Window |
|----------|-------|--------|
| API Requests | 100/min | Per API key |
| Agent Triggers | 50/min | Per agent |
| Actions Per Agent | 200/hour | Per agent |
| Webhook Deliveries | 500/min | Per endpoint |

## Instructions

### Step 1: API-Level Rate Limiter

### Step 2: Agent Action Budget

Track actions per agent to prevent hitting hourly limits.

### Step 3: Webhook Rate Management

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 API response | Exceeded 100 RPM | Rate limiter with backoff |
| Agent actions blocked | Exceeded 200 actions/hour | Track and budget agent actions |
| Webhook flood | External trigger storm | Rate limit webhook processing |
| Agent stalled | Hit action limit mid-workflow | Monitor remaining budget |

## Examples

### Status Dashboard
## Resources
- [Lindy API Docs](https://docs.lindy.ai)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [API implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.