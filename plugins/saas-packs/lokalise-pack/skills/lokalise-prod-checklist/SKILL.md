---
name: lokalise-prod-checklist
description: |
  Execute Lokalise production deployment checklist and rollback procedures.
  Use when deploying Lokalise integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "lokalise production", "deploy lokalise",
  "lokalise go-live", "lokalise launch checklist".
allowed-tools: Read, Bash(lokalise2:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Prod Checklist

## Overview
Complete checklist for deploying Lokalise integrations to production.

## Prerequisites
- Staging environment tested and verified
- Production API token available
- Deployment pipeline configured
- Monitoring and alerting ready

## Instructions

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Deployed Lokalise integration
- Health checks passing
- Monitoring active
- Rollback procedure documented

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| API Down | 5xx errors > 5/min | P1 |
| Translation Missing | 404 on key lookup | P2 |
| Rate Limited | 429 errors > 10/min | P2 |
| Auth Failures | 401/403 errors > 0 | P1 |
| High Latency | p99 > 3000ms | P3 |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Lokalise Status](https://status.lokalise.com)
- [Lokalise Support](mailto:support@lokalise.com)

## Next Steps
For version upgrades, see `lokalise-upgrade-migration`.
