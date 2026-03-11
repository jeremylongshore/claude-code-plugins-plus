---
name: lokalise-deploy-integration
description: |
  Deploy Lokalise integrations to Vercel, Netlify, and Cloud Run platforms.
  Use when deploying apps with Lokalise translations to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy lokalise", "lokalise Vercel",
  "lokalise production deploy", "lokalise Netlify", "lokalise Cloud Run".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(netlify:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Deploy Integration

## Overview
Deploy applications with Lokalise translations to popular platforms with proper secrets management.

## Prerequisites
- Lokalise API token for production
- Platform CLI installed (vercel, netlify, or gcloud)
- Application code ready for deployment
- Translations synced and verified

## Instructions
1. **Vercel Deployment**
2. **Netlify Deployment**
3. **Google Cloud Run**
4. **OTA (Over-the-Air) Updates for Mobile**
5. **Health Check Endpoint**
6. **Instructions**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Application deployed to production
- Lokalise secrets securely configured
- Translations bundled with deployment
- Health check endpoint functional

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing translations | Pre-build failed | Check build logs for Lokalise errors |
| Secret not found | Missing configuration | Add secret via platform CLI |
| Build timeout | Large translations | Cache translations or increase timeout |
| OTA fails | Network/token issue | Fall back to bundled translations |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Netlify Documentation](https://docs.netlify.com)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Lokalise OTA](https://docs.lokalise.com/en/articles/1400660-over-the-air-sdk-for-ios-and-android)

## Next Steps
For webhook handling, see `lokalise-webhooks-events`.