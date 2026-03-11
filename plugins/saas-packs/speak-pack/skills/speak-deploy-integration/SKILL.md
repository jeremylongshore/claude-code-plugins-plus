---
name: speak-deploy-integration
description: |
  Deploy Speak language learning integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Speak-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy speak", "speak Vercel",
  "speak production deploy", "speak Cloud Run", "speak Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Deploy Integration

## Overview
Deploy Speak-powered language learning applications to popular platforms with proper secrets management.

## Prerequisites
- Speak API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented
- Audio storage configured

## Instructions
1. **Vercel Deployment**
2. **Fly.io Deployment**
3. **Google Cloud Run**
4. **Environment Configuration Pattern**
5. **Health Check Endpoint**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Application deployed to production
- Speak secrets securely configured
- Health check endpoint functional
- Audio processing infrastructure ready
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build or audio deps | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |
| Audio timeout | Processing too slow | Increase memory/CPU |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Speak Deploy Guide](https://developer.speak.com/docs/deploy)

## Next Steps
For webhook handling, see `speak-webhooks-events`.