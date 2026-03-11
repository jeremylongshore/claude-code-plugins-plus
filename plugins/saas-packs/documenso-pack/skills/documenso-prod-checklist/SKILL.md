---
name: documenso-prod-checklist
description: |
  Execute Documenso production deployment checklist and rollback procedures.
  Use when deploying Documenso integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "documenso production", "deploy documenso",
  "documenso go-live", "documenso launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Production Checklist

## Overview
Complete checklist for deploying Documenso document signing integrations to production.

## Prerequisites
- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured
- Monitoring and alerting ready

## Instructions

### Step 1: Pre-Deployment Checklist
Implement pre-deployment checklist.
### Step 2: Deployment Procedure
curl -f https://staging.yourapp.com/health
### Step 3: Rollback Procedure
kubectl rollout undo deployment/signing-service
### Step 4: Post-Deployment Verification
npm run test:smoke

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Pre-Deployment Checklist
- Deployment Procedure
- Rollback Procedure
- Post-Deployment Verification

## Error Handling
| Alert | Condition | Response |
|-------|-----------|----------|
| Deploy failed | CI/CD error | Check logs, retry |
| Health check failed | Documenso down | Implement degraded mode |
| Rollback needed | Error spike | Execute rollback |
| Rate limits hit | Too many requests | Reduce throughput |

## Resources
- [Documenso Status](https://status.documenso.com)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Feature Flags Best Practices](https://launchdarkly.com/blog/feature-flag-best-practices/)

## Next Steps
For version upgrades, see `documenso-upgrade-migration`.
