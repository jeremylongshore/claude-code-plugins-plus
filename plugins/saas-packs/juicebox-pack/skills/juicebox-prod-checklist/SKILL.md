---
name: juicebox-prod-checklist
description: |
  Execute Juicebox production deployment checklist.
  Use when preparing for production launch, validating deployment readiness,
  or performing pre-launch reviews.
  Trigger with phrases like "juicebox production", "deploy juicebox prod",
  "juicebox launch checklist", "juicebox go-live".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Production Checklist

## Overview
Complete production readiness checklist for Juicebox integration deployment.

## Prerequisites
- Development and staging testing complete
- Production environment provisioned
- Monitoring infrastructure ready

## Instructions
- Production Readiness Checklist
- Validation Scripts
- Go-Live Checklist
- Day-of-Launch Checklist

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Production Best Practices](https://juicebox.ai/docs/production)
- [Status Page](https://status.juicebox.ai)

## Next Steps
After production launch, see `juicebox-upgrade-migration` for SDK updates.
