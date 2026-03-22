---
name: vercel-deploy-integration
description: |
  Deploy and manage Vercel production deployments with promotion, rollback, and multi-region strategies.
  Use when deploying to production, configuring deployment regions,
  or setting up blue-green deployment patterns on Vercel.
  Trigger with phrases like "deploy vercel", "vercel production deploy",
  "vercel promote", "vercel rollback", "vercel regions".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, deployment, production, rollback]

---
# Vercel Deploy Integration

## Overview
Deploy Vercel applications to production using CLI, API, and Git-triggered workflows. Covers deployment promotion, instant rollback, rolling releases, multi-region function configuration, and deploy hooks for headless CMS integration.

## Prerequisites
- Vercel project linked and configured
- Production environment variables set
- Custom domain configured (optional)
- `VERCEL_TOKEN` for API-based deployments

## Instructions

### Step 1: Production Deploy Methods
```bash
# Method 1: CLI direct production deploy
vercel --prod

# Method 2: Promote a preview deployment to production
vercel promote https://my-app-preview-xxx.vercel.app

# Method 3: API-based deployment
curl -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "target": "production",
    "gitSource": {
      "type": "github",
      "repoId": "123456789",
      "ref": "main",
      "sha": "'$(git rev-parse HEAD)'"
    }
  }'

# Method 4: Deploy Hook (for CMS-triggered rebuilds)
curl -X POST "https://api.vercel.com/v1/integrations/deploy/prj_xxx/hook_xxx"
```

### Step 2: Instant Rollback
```bash
# Roll back to the previous production deployment (no rebuild)
vercel rollback

# Roll back to a specific deployment
vercel rollback dpl_xxxxxxxxxxxx

# Verify the rollback
vercel ls --prod
curl -s https://yourdomain.com/api/health | jq .

# Via API — promote a known-good deployment
curl -X POST "https://api.vercel.com/v9/projects/my-app/promote" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deploymentId": "dpl_known_good_id"}'
```

Key points:
- Instant rollback swaps production traffic without rebuilding
- The rolled-back deployment retains its original environment variables
- All production domains immediately point to the rolled-back deployment

### Step 3: Rolling Releases (Gradual Rollout)
Configure rolling releases in the dashboard under **Settings > Rolling Releases**:

```json
// vercel.json — rolling release config
{
  "rollingRelease": {
    "enabled": true,
    "stages": [
      { "targetPercentage": 10, "duration": 300 },
      { "targetPercentage": 50, "duration": 600 },
      { "targetPercentage": 100 }
    ]
  }
}
```

This routes 10% of traffic to the new deployment for 5 minutes, then 50% for 10 minutes, then 100%. If errors spike during any stage, rollback instantly.

### Step 4: Multi-Region Function Configuration
```json
// vercel.json — deploy functions to specific regions
{
  "regions": ["iad1", "sfo1", "cdg1", "hnd1"],
  "functions": {
    "api/user.ts": {
      "memory": 1024,
      "maxDuration": 30
    },
    "api/heavy-compute.ts": {
      "memory": 3008,
      "maxDuration": 60,
      "regions": ["iad1"]
    }
  }
}
```

Available regions:
| Region | Location | Code |
|--------|----------|------|
| Washington, D.C. | US East | `iad1` |
| San Francisco | US West | `sfo1` |
| Paris | Europe | `cdg1` |
| Tokyo | Asia | `hnd1` |
| Sydney | Australia | `syd1` |
| S. Paulo | South America | `gru1` |
| London | Europe | `lhr1` |

### Step 5: Deploy Hooks (CMS Triggers)
Create deploy hooks in **Settings > Git > Deploy Hooks**:

```bash
# Create via dashboard, then trigger with POST
curl -X POST "https://api.vercel.com/v1/integrations/deploy/prj_xxx/hook_xxx"

# Common CMS integrations:
# Contentful — webhook URL → Vercel deploy hook
# Sanity — GROQ listener → deploy hook
# Strapi — lifecycle hook → deploy hook
```

### Step 6: Deployment Monitoring
```bash
# List recent production deployments
vercel ls --prod --limit=5

# Check deployment state
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v6/deployments?target=production&limit=5&projectId=prj_xxx" \
  | jq '.deployments[] | {uid, url, state, createdAt}'

# Monitor deployment logs in real-time
vercel logs https://yourdomain.com --follow
```

## Deploy Lifecycle

```
git push main
  → Vercel builds (BUILDING)
    → Build succeeds (READY)
      → Traffic routes to new deployment
        → Old deployment kept for instant rollback
```

## Output
- Production deployment live via CLI, API, or Git push
- Instant rollback configured to previous deployment
- Rolling releases for gradual traffic shifting
- Function regions optimized for user geography
- Deploy hooks for CMS-triggered rebuilds

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `DEPLOYMENT_BLOCKED` | Deployment freeze or branch protection | Disable freeze in Settings or use --force |
| Promotion fails | Preview deployment has different env vars | Verify env vars match between preview and production |
| Rolling release stuck | Error threshold exceeded | Fix the code, then restart the rollout |
| Deploy hook returns 404 | Hook deleted or project ID wrong | Recreate the hook in Settings > Git |
| Region not available | Plan doesn't support multi-region | Upgrade to Pro or Enterprise |

## Resources
- [Deploying to Vercel](https://vercel.com/docs/deployments)
- [Instant Rollback](https://vercel.com/docs/instant-rollback)
- [Rolling Releases](https://vercel.com/docs/rolling-releases)
- [Promoting Deployments](https://vercel.com/docs/deployments/promoting-a-deployment)
- [Deploy Hooks](https://vercel.com/docs/deploy-hooks)
- [Function Regions](https://vercel.com/docs/functions/configuring-functions)

## Next Steps
For webhook integration, see `vercel-webhooks-events`.
