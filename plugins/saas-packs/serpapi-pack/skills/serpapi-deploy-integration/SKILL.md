---
name: serpapi-deploy-integration
description: |
  Deploy SerpApi integrations to production platforms.
  Use when deploying SerpApi-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy serpapi", "serpapi production",
  "serpapi production deploy", "serpapi CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi Deploy Integration

## Overview

Deploy using SerpApi's native deployment tools. Configuration lives in the
project repo and deploys trigger via git push or CLI commands.


## Prerequisites
- SerpApi API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Vercel Deployment

### Environment Setup
```bash
vercel secrets add serpapi_api_key sk_live_***
vercel secrets add serpapi_webhook_secret whsec_***
vercel link
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "SERPAPI_API_KEY": "@serpapi_api_key"
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
app = "my-serpapi-app"
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
fly secrets set SERPAPI_API_KEY=sk_live_***
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const serpapiStatus = await checkSerpApiConnection();

  return Response.json({
    status: serpapiStatus ? 'healthy' : 'degraded',
    services: {
      serpapi: serpapiStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store SerpApi API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with SerpApi integration.

### Step 4: Verify Health
Test the health check endpoint to confirm SerpApi connectivity.

## Output
- Application deployed to production
- SerpApi secrets securely configured
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
- [SerpApi Deploy Guide](https://docs.serpapi.com/deploy)

## Next Steps
For webhook handling, see `serpapi-webhooks-events`.