---
name: supabase-deploy-integration
description: |
  Deploy Supabase integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Supabase-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy supabase", "supabase Vercel",
  "supabase production deploy", "supabase Cloud Run", "supabase Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Deploy Integration

## Prerequisites
- Supabase API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Supabase API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Supabase integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Supabase connectivity.

## Output
- Application deployed to production
- Supabase secrets securely configured
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
- [Supabase Deploy Guide](https://supabase.com/docs/deploy)

## Overview

Deploy Supabase integrations to Vercel, Fly.