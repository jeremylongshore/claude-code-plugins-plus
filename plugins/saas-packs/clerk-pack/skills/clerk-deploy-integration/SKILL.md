---
name: clerk-deploy-integration
description: |
  Configure Clerk for deployment on various platforms.
  Use when deploying to Vercel, Netlify, Railway, or other platforms,
  or when setting up production environment.
  Trigger with phrases like "deploy clerk", "clerk Vercel",
  "clerk Netlify", "clerk production deploy", "clerk Railway".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(netlify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Deploy Integration

## Overview
Deploy Clerk-authenticated applications to various hosting platforms.

## Prerequisites
- Clerk production instance configured
- Production API keys ready
- Hosting platform account

## Instructions
1. Step 1: Configure Environment Variables
2. Step 2: Configure Clerk Dashboard
3. Step 3: Deploy
4. Step 1: Configure Environment Variables
5. Step 2: Create Netlify Functions for API
6. Step 1: Configure Railway
7. Step 2: Set Environment Variables

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Platform-specific deployment configuration
- Environment variables configured
- Webhook endpoints ready
- Production domain configured

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 500 on sign-in | Missing secret key | Add CLERK_SECRET_KEY to platform |
| Webhook fails | Wrong endpoint URL | Update URL in Clerk Dashboard |
| CORS error | Domain not allowed | Add domain to Clerk allowed origins |
| Redirect loop | Wrong sign-in URL | Check CLERK_SIGN_IN_URL config |

## Resources
- [Vercel Deployment](https://clerk.com/docs/deployments/deploy-to-vercel)
- [Netlify Deployment](https://clerk.com/docs/deployments/deploy-to-netlify)
- [Railway Guide](https://railway.app/docs)

## Next Steps
Proceed to `clerk-webhooks-events` for webhook configuration.

## Examples

**Basic usage**: Apply clerk deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk deploy integration for production environments with multiple constraints and team-specific requirements.