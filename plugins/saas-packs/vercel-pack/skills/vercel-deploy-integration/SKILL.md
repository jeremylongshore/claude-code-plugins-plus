---
name: vercel-deploy-integration
description: |
  Deploy Vercel integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Vercel-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy vercel", "vercel Vercel",
  "vercel production deploy", "vercel Cloud Run", "vercel Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Deploy Integration

## Prerequisites
- Vercel API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Vercel API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Vercel integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Vercel connectivity.

## Output
- Application deployed to production
- Vercel secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vercel Deploy Guide](https://vercel.com/docs/deploy)
