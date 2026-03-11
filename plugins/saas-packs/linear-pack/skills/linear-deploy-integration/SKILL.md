---
name: linear-deploy-integration
description: |
  Deploy Linear-integrated applications and track deployments.
  Use when deploying to production, setting up deployment tracking,
  or integrating Linear with deployment platforms.
  Trigger with phrases like "deploy linear integration", "linear deployment",
  "linear vercel", "linear production deploy", "track linear deployments".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Deploy Integration

## Overview
Deploy Linear-integrated applications and track deployments in Linear.

## Prerequisites
- Working Linear integration
- Deployment platform account (Vercel, Railway, Cloud Run, etc.)
- CI/CD pipeline configured

## Instructions
- Step 1: Vercel Deployment
- Step 2: Google Cloud Run Deployment
- Step 3: Railway Deployment
- Step 4: Deployment Tracking in Linear
- Step 5: GitHub Actions Deployment Workflow
- Step 6: Rollback Tracking

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Secret not found` | Missing env var | Configure secrets on platform |
| `Webhook timeout` | Long processing | Increase function timeout |
| `Connection refused` | Firewall blocking | Check egress rules |

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Linear Deployment Tracking](https://linear.app/docs/git-integrations)

## Next Steps
Set up webhooks with `linear-webhooks-events`.
