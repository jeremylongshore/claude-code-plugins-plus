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
1. Step 1: Vercel Deployment
2. Step 2: Google Cloud Run Deployment
3. Step 3: Railway Deployment
4. Step 4: Deployment Tracking in Linear
5. Step 5: GitHub Actions Deployment Workflow
6. Step 6: Rollback Tracking

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

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [deployment implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply linear deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear deploy integration for production environments with multiple constraints and team-specific requirements.