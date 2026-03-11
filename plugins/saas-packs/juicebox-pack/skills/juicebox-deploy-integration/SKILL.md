---
name: juicebox-deploy-integration
description: |
  Deploy Juicebox integrations to production.
  Use when deploying to cloud platforms, configuring production environments,
  or setting up infrastructure for Juicebox.
  Trigger with phrases like "deploy juicebox", "juicebox production deploy",
  "juicebox infrastructure", "juicebox cloud setup".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Deploy Integration

## Overview
Deploy Juicebox integrations to production cloud environments.

## Prerequisites
- CI pipeline configured
- Cloud provider account (AWS, GCP, or Azure)
- Production API key secured

## Instructions
- Step 1: Configure Secret Management
- Step 2: Create Deployment Configuration
- Step 3: Configure Health Checks
- Step 4: Deployment Script

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Secret management configuration
- Docker/Kubernetes manifests
- Health check endpoints
- Deployment scripts

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | IAM permissions | Grant access to secret |
| Health check fails | API connectivity | Check network policies |
| Rollout stuck | Resource limits | Adjust resource requests |

## Resources
- [AWS Deployment Guide](https://juicebox.ai/docs/deploy/aws)
- [GCP Deployment Guide](https://juicebox.ai/docs/deploy/gcp)

## Next Steps
After deployment, see `juicebox-webhooks-events` for event handling.
