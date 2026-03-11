---
name: lindy-deploy-integration
description: |
  Configure deployment pipelines for Lindy AI integrations.
  Use when deploying to production, setting up staging environments,
  or automating agent deployments.
  Trigger with phrases like "deploy lindy", "lindy deployment",
  "lindy production deploy", "release lindy agents".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy AI Deploy Integration

## Overview
Deploy Lindy AI agent integrations to production environments. Lindy agents run on Lindy's managed infrastructure, so deployment focuses on configuring your application's connection to Lindy agents, managing API credentials, and setting up webhook endpoints that Lindy agents interact with.

## Prerequisites
- Lindy account with agents configured
- Lindy API key stored in `LINDY_API_KEY` environment variable
- Application endpoints ready for Lindy agent callbacks
- Deployment platform CLI (Vercel, Docker, etc.)

## Instructions

### Step 1: Configure Agent Connection
### Step 2: Docker Deployment
### Step 3: Vercel Deployment
### Step 4: Production Agent Trigger
### Step 5: Health Check

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent not found | Invalid agent ID | Verify agent IDs in Lindy dashboard |
| Webhook unreachable | Wrong URL or HTTPS | Ensure public HTTPS endpoint |
| API key invalid | Key revoked | Regenerate in Lindy settings |
| Agent timeout | Complex task | Increase agent timeout in Lindy config |

## Examples


**Basic usage**: Apply lindy deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Lindy AI Documentation](https://docs.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
For webhook handling, see `lindy-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [CI/CD implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.