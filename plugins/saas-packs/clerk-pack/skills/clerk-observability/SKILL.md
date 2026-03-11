---
name: clerk-observability
description: |
  Implement monitoring, logging, and observability for Clerk authentication.
  Use when setting up monitoring, debugging auth issues in production,
  or implementing audit logging.
  Trigger with phrases like "clerk monitoring", "clerk logging",
  "clerk observability", "clerk metrics", "clerk audit log".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Observability

## Overview
Implement comprehensive monitoring, logging, and observability for Clerk authentication.

## Prerequisites
- Clerk integration working
- Monitoring platform (DataDog, New Relic, Sentry, etc.)
- Logging infrastructure

## Instructions
- Step 1: Authentication Event Logging
- Step 2: Middleware Monitoring
- Step 3: Session Analytics
- Step 4: Webhook Event Tracking
- Step 5: Error Tracking with Sentry
- Step 6: Health Check Endpoint

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Authentication event logging
- Performance monitoring
- Error tracking integration
- Health check endpoints

## Error Handling
| Issue | Monitoring Action |
|-------|-------------------|
| High auth latency | Alert on p95 > 200ms |
| Failed webhooks | Alert on failure rate > 1% |
| Session anomalies | Track unusual session patterns |
| API errors | Capture with Sentry context |

## Resources
- [Clerk Dashboard Analytics](https://dashboard.clerk.com)
- [Sentry Integration](https://docs.sentry.io)
- [DataDog APM](https://docs.datadoghq.com/tracing)

## Next Steps
Proceed to `clerk-incident-runbook` for incident response procedures.
