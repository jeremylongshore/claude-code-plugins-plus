---
name: guidewire-prod-checklist
description: |
  Production deployment readiness checklist for Guidewire InsuranceSuite Cloud.
  Use when preparing for production deployment, conducting go-live reviews,
  or validating environment readiness.
  Trigger with phrases like "guidewire production", "go-live checklist",
  "deployment readiness", "production review", "guidewire cloud deploy".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Guidewire Production Checklist

## Overview
Comprehensive production readiness checklist for Guidewire InsuranceSuite Cloud deployment, covering security, performance, monitoring, and operational readiness.

## Prerequisites
- Completed development and testing phases
- Access to Guidewire Cloud Console
- Stakeholder sign-off on functionality

## Instructions

### Step 1: Production Readiness Checklist
Implement production readiness checklist.
### Step 2: Validation Scripts
// Production health check implementation
### Step 3: Go-Live Runbook
1. [ ] Final code freeze confirmed
### Step 4: Monitoring Dashboard Queries
dashboards:
### Step 5: Rollback Procedure
echo "=== Starting Rollback ==="

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Production Readiness Checklist
- Validation Scripts
- Go-Live Runbook
- Monitoring Dashboard Queries
- Rollback Procedure

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Guidewire Cloud Operations](https://docs.guidewire.com/cloud/)
- [InsuranceSuite Best Practices](https://docs.guidewire.com/education/)

## Next Steps
For upgrade and migration procedures, see `guidewire-upgrade-migration`.
