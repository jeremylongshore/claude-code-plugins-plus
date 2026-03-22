---
name: replit-deploy-integration
description: |
  Deploy Replit apps with Autoscale, Reserved VM, and Static deployment types.
  Use when deploying to production, configuring deployment settings, setting up
  custom domains, or managing deployment secrets and health checks.
  Trigger with phrases like "deploy replit", "replit deployment",
  "replit autoscale", "replit reserved VM", "replit static deploy", "replit custom domain".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, deployment, hosting]

---
# Replit Deploy Integration

## Overview
Deploy applications on Replit's hosting platform. Three deployment types: Static (free, frontend-only), Autoscale (scales to zero, pay per request), and Reserved VM (always-on, fixed cost). Includes custom domain setup, health checks, rollbacks, and deployment monitoring.

## Prerequisites
- Replit Core, Pro, or Teams plan (deployment access)
- Application working in Workspace ("Run" button)
- Custom domain (optional) with DNS access

## Deployment Types

| Type | Best For | Pricing | Scale |
|------|----------|---------|-------|
| **Static** | HTML/CSS/JS frontends | Free | CDN-backed, auto-cached |
| **Autoscale** | Variable traffic APIs | Per request | 0 to N instances |
| **Reserved VM** | Always-on services | $0.20+/day | Fixed resources |

## Instructions

### Step 1: Configure `.replit` for Deployment
```toml
# .replit — Autoscale deployment (most common)
entrypoint = "src/index.ts"
run = "npx tsx src/index.ts"

[nix]
channel = "stable-24_05"

[env]
NODE_ENV = "production"

[deployment]
run = ["sh", "-c", "npx tsx src/index.ts"]
build = ["sh", "-c", "npm ci --production && npm run build"]
deploymentTarget = "autoscale"
```

**Reserved VM:**
```toml
[deployment]
run = ["sh", "-c", "node dist/index.js"]
build = ["sh", "-c", "npm ci && npm run build"]
deploymentTarget = "cloudrun"
```

**Static:**
```toml
[deployment]
deploymentTarget = "static"
publicDir = "dist"
build = ["sh", "-c", "npm ci && npm run build"]
```

### Step 2: Configure Secrets for Production
```markdown
Workspace Secrets auto-sync to Deployments (2025+).

1. Click lock icon (Secrets) in sidebar
2. Add production secrets:
   - DATABASE_URL (auto-populated by Replit PostgreSQL)
   - API_KEY, JWT_SECRET, etc.
3. Verify in Deployment Settings > Environment Variables
```

### Step 3: Add Health Check Endpoint
Replit monitors your deployment via health checks. Always include one:

```typescript
// src/routes/health.ts
import { Router } from 'express';
import { pool } from '../services/db';

const router = Router();

router.get('/health', async (req, res) => {
  const checks: Record<string, any> = {
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  };

  // Check database if configured
  if (process.env.DATABASE_URL) {
    try {
      await pool.query('SELECT 1');
      checks.database = 'connected';
    } catch {
      checks.database = 'disconnected';
      checks.status = 'degraded';
    }
  }

  // Replit-specific metadata
  checks.repl = process.env.REPL_SLUG;
  checks.region = process.env.REPLIT_DEPLOYMENT_REGION;

  const statusCode = checks.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(checks);
});

export default router;
```

### Step 4: Deploy
```markdown
Via Replit UI:
1. Click "Deploy" button in the top bar
2. Select deployment type:
   - Static: for frontend-only apps
   - Autoscale: scales to zero when idle
   - Reserved VM: always-on, choose machine size
3. Configure machine size (Autoscale/VM):
   - 0.25 vCPU / 512 MB — lightweight APIs
   - 0.5 vCPU / 1 GB — standard web apps
   - 2 vCPU / 4 GB — compute-heavy apps
   - 4+ vCPU / 8-16 GB — production workloads
4. Click "Deploy"
5. Monitor build output in the deploy console
```

### Step 5: Custom Domain Setup
```markdown
1. Go to Deployment Settings > Custom Domain
2. Enter your domain: app.example.com
3. Add DNS record at your registrar:
   Type: CNAME
   Name: app
   Value: your-repl-slug.replit.app
4. Wait for SSL auto-provisioning (1-5 minutes)
5. Verify:
```
```bash
# Verify DNS
dig app.example.com CNAME

# Verify SSL
curl -I https://app.example.com

# Verify health
curl -sf https://app.example.com/health | jq .
```

For Replit-purchased domains:
- DNS managed in Replit dashboard
- MX records supported for custom email
- SSL auto-provisioned

### Step 6: Deployment Rollback
Replit supports one-click rollback to any previous successful deployment.

```markdown
1. Go to Deployment Settings > History
2. View list of past deployments with timestamps
3. Click "Rollback" on the desired version
4. Deployment reverts immediately
5. Verify health endpoint after rollback
```

### Step 7: Post-Deploy Verification
```bash
set -euo pipefail
DEPLOY_URL="https://your-app.replit.app"

echo "=== Deployment Verification ==="

# Health check
echo -n "Health: "
curl -sf "$DEPLOY_URL/health" | jq -r '.status'

# Response time
echo -n "Response time: "
curl -s -o /dev/null -w "%{time_total}s\n" "$DEPLOY_URL/"

# SSL certificate
echo -n "SSL: "
curl -sI "$DEPLOY_URL" | grep -i "strict-transport" && echo "OK" || echo "Missing HSTS"

# Autoscale cold start test
echo "Cold start test: wait 10 min, then curl again"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy fails at build | Dependency error | Test `npm ci && npm run build` locally first |
| 503 after deploy | App crashes on start | Check deployment logs, verify secrets |
| Port mismatch | Not using PORT env | `app.listen(process.env.PORT \|\| 3000)` |
| Cold start slow (>10s) | Heavy imports on startup | Lazy-load non-critical modules |
| Custom domain 404 | DNS not propagated | Wait, or verify CNAME record |
| SSL not provisioning | Wrong DNS record | Must be CNAME to `.replit.app` |

## Resources
- [Autoscale Deployments](https://blog.replit.com/autoscale)
- [Reserved VM Deployments](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)
- [Static Deployments](https://docs.replit.com/cloud-services/deployments/static-deployments)
- [Deployment Rollbacks](https://blog.replit.com/introducing-deployment-rollbacks)
- [Custom Domains](https://docs.replit.com/hosting/custom-domains)
- [Monitoring Deployments](https://docs.replit.com/cloud-services/deployments/monitoring-a-deployment)

## Next Steps
For multi-environment setup, see `replit-multi-env-setup`.
