---
name: windsurf-deploy-integration
description: |
  Deploy Windsurf integrations to production platforms.
  Use when deploying Windsurf-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy windsurf", "windsurf production",
  "windsurf production deploy", "windsurf CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, windsurf]
---

# Windsurf Deploy Integration

## Overview

Deploy using Windsurf's native deployment tools. Configuration lives in the
project repo and deploys trigger via git push or CLI commands.


## Prerequisites
- Windsurf API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Vercel Deployment

### Environment Setup
```bash
vercel secrets add windsurf_api_key sk_live_***
vercel secrets add windsurf_webhook_secret whsec_***
vercel link
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "WINDSURF_API_KEY": "@windsurf_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

## Fly.io Deployment

### fly.toml
```toml
app = "my-windsurf-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
```

### Secrets
```bash
fly secrets set WINDSURF_API_KEY=sk_live_***
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const windsurfStatus = await checkWindsurfConnection();

  return Response.json({
    status: windsurfStatus ? 'healthy' : 'degraded',
    services: {
      windsurf: windsurfStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Windsurf API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Windsurf integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Windsurf connectivity.

## Output
- Application deployed to production
- Windsurf secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Windsurf Deploy Guide](https://docs.windsurf.com/deploy)

## Next Steps
For webhook handling, see `windsurf-webhooks-events`.