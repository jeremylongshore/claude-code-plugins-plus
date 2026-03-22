---
name: hex-prod-checklist
description: |
  Execute Hex production deployment checklist and rollback procedures.
  Use when deploying Hex integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "hex production", "deploy hex",
  "hex go-live", "hex launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Production Checklist

## Checklist

### API Access
- [ ] Production API token in secrets vault
- [ ] Token has "Run projects" scope
- [ ] Token expiration > 90 days (set calendar reminder)

### Projects
- [ ] All orchestrated projects published
- [ ] Input parameters documented
- [ ] Error handling for ERRORED/KILLED runs

### Orchestration
- [ ] Rate limits respected (20/min, 60/hr)
- [ ] Run timeout configured
- [ ] Retry logic for transient failures

### Monitoring
- [ ] Run status polling in place
- [ ] Alert on ERRORED runs
- [ ] Track run durations for regression

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
