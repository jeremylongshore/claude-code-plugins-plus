---
name: lindy-prod-checklist
description: |
  Production readiness checklist for Lindy AI deployments.
  Use when preparing for production, reviewing deployment,
  or auditing production setup.
  Trigger with phrases like "lindy production", "lindy prod ready",
  "lindy go live", "lindy deployment checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Prod Checklist

## Overview
Comprehensive production readiness checklist for Lindy AI deployments.

## Prerequisites
- Completed development and testing
- Production Lindy account
- Deployment infrastructure ready

## Production Checklist

### Authentication & Security
### Agent Configuration
### Monitoring & Observability
### Performance & Reliability
### Compliance & Documentation
## Implementation

### Health Check Endpoint
### Pre-Deployment Validation

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Complete production checklist
- Health check implementation
- Pre-deployment validation script
- Go/no-go criteria defined

## Error Handling
| Check | Failure Action | Severity |
|-------|----------------|----------|
| API Key | Block deploy | Critical |
| Connectivity | Retry/alert | High |
| Agents exist | Warning | Medium |
| Monitoring | Document gap | Medium |

## Examples

### Deployment Gate Script
## Resources
- [Lindy Production Guide](https://docs.lindy.ai/production)
- [SLA Information](https://lindy.ai/sla)
- [Support](https://support.lindy.ai)

## Next Steps
Proceed to `lindy-upgrade-migration` for version upgrades.
