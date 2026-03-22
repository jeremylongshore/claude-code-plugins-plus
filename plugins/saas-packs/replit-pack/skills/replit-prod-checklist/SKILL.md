---
name: replit-prod-checklist
description: |
  Execute Replit production deployment checklist with rollback and health monitoring.
  Use when deploying Replit apps to production, preparing for launch,
  or implementing go-live procedures with Autoscale or Reserved VM.
  Trigger with phrases like "replit production", "deploy replit",
  "replit go-live", "replit launch checklist", "replit prod ready".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, deployment, production]

---
# Replit Production Checklist

## Overview
Complete checklist for deploying Replit apps to production using Autoscale or Reserved VM deployments. Covers configuration, secrets, health checks, custom domains, rollback procedures, and monitoring.

## Prerequisites
- Replit Core, Pro, or Teams plan (deployment access)
- App tested and working in Workspace
- PostgreSQL database provisioned (if needed)
- Custom domain (optional) with DNS access

## Production Deployment Checklist

### Phase 1: Configuration
- [ ] `.replit` deployment section configured:
```toml
[deployment]
run = ["sh", "-c", "npm start"]
build = ["sh", "-c", "npm ci --production && npm run build"]
deploymentTarget = "autoscale"  # or "cloudrun" for Reserved VM
```
- [ ] `replit.nix` includes only required system packages (trim dev-only deps)
- [ ] `NODE_ENV` set to `"production"` in `.replit` env section
- [ ] Port reads from `process.env.PORT`

### Phase 2: Secrets
- [ ] All secrets configured in Replit Secrets tab
- [ ] Secrets sync enabled (Workspace <-> Deployment)
- [ ] No hardcoded credentials in source code
- [ ] Startup validates all required secrets:
```typescript
const REQUIRED = ['DATABASE_URL', 'JWT_SECRET'];
const missing = REQUIRED.filter(k => !process.env[k]);
if (missing.length) {
  console.error(`FATAL: Missing secrets: ${missing.join(', ')}`);
  process.exit(1);
}
```

### Phase 3: Health Check
- [ ] `/health` endpoint exists and checks dependencies:
```typescript
app.get('/health', async (req, res) => {
  const checks = {
    db: false,
    uptime: process.uptime(),
    memory: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
  };

  try {
    await pool.query('SELECT 1');
    checks.db = true;
  } catch {}

  const status = checks.db ? 200 : 503;
  res.status(status).json({ status: status === 200 ? 'healthy' : 'degraded', ...checks });
});
```
- [ ] Health endpoint does NOT expose secrets or internal paths
- [ ] Health endpoint responds within 5 seconds

### Phase 4: Error Handling
- [ ] Global error handler catches uncaught exceptions:
```typescript
// Never expose stack traces in production
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err.message);
  res.status(500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message,
  });
});

process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('Unhandled rejection:', reason);
});
```
- [ ] Rate limiting on public endpoints
- [ ] Input validation on all user data (Zod, Joi, or manual)

### Phase 5: Deploy

**Via Replit UI:**
1. Click "Deploy" button in top bar
2. Choose type:
   - **Static**: Frontend-only (HTML/CSS/JS), free
   - **Autoscale**: Scales to zero, pay per request (best for variable traffic)
   - **Reserved VM**: Always-on, fixed cost (best for consistent traffic)
3. Select machine size (0.25-8 vCPU)
4. Click "Deploy"

**Via `.replit` config (automatic on push):**
```toml
[deployment]
run = ["sh", "-c", "node dist/index.js"]
build = ["sh", "-c", "npm ci --production && npm run build"]
deploymentTarget = "autoscale"
```

### Phase 6: Custom Domain
```markdown
1. Deployment Settings > Custom Domain
2. Enter domain: app.example.com
3. Add DNS record at your registrar:
   CNAME: app -> your-repl-slug.replit.app
4. Wait 1-5 minutes for SSL auto-provisioning
5. Verify: curl -I https://app.example.com
```
For Replit-purchased domains: manage DNS directly in Replit dashboard.

### Phase 7: Post-Deploy Verification
```bash
set -euo pipefail
DEPLOY_URL="https://your-app.replit.app"

# Health check
curl -sf "$DEPLOY_URL/health" | jq .

# Response time
curl -s -o /dev/null -w "HTTP %{http_code}, %{time_total}s\n" "$DEPLOY_URL/"

# Headers check
curl -sI "$DEPLOY_URL" | grep -iE "(server|content-type|x-)"
```

### Phase 8: Rollback Plan
Replit Deployments support one-click rollback to any previous successful deployment:
1. Go to Deployment Settings > History
2. Find the last known-good deployment
3. Click "Rollback to this version"
4. Verify health endpoint after rollback

## Monitoring Recommendations
| Signal | Warning | Critical |
|--------|---------|----------|
| Health check | 1 failure | 3 consecutive failures |
| Response time (p95) | > 2s | > 5s |
| Error rate | > 1% | > 5% |
| Memory usage | > 75% of limit | > 90% |
| Cold start (Autoscale) | > 5s | > 15s |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy fails at build | Missing dependency | Check build logs, ensure `npm ci` works |
| 503 after deploy | App crashing on start | Check deployment logs, verify secrets |
| Cold start too slow | Heavy imports | Lazy-load non-critical modules |
| Custom domain not working | DNS not propagated | Wait or verify CNAME record |

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Deployment Rollbacks](https://blog.replit.com/introducing-deployment-rollbacks)
- [Custom Domains](https://docs.replit.com/hosting/custom-domains)
- [Replit Status](https://status.replit.com)

## Next Steps
For version upgrades, see `replit-upgrade-migration`.
