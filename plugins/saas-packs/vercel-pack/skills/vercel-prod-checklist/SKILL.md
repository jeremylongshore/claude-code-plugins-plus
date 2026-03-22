---
name: vercel-prod-checklist
description: |
  Vercel production deployment checklist with rollback and promotion procedures.
  Use when deploying to production, preparing for launch,
  or implementing go-live and instant rollback procedures.
  Trigger with phrases like "vercel production", "deploy vercel prod",
  "vercel go-live", "vercel launch checklist", "vercel promote".
allowed-tools: Read, Bash(vercel:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, deployment, production, checklist]

---
# Vercel Prod Checklist

## Overview
Complete pre-production checklist for Vercel deployments covering environment variables, domain configuration, performance, security, monitoring, and instant rollback procedures.

## Prerequisites
- Staging deployment tested and verified
- Production domain DNS configured
- Production environment variables set
- Monitoring and alerting configured

## Instructions

### Step 1: Pre-Deploy Verification
```bash
# Verify production env vars are set
vercel env ls --environment=production

# Required production variables (example):
# DATABASE_URL — production database
# API_SECRET — production API key (type: sensitive)
# NEXT_PUBLIC_API_URL — public API endpoint
# SENTRY_DSN — error tracking

# Build locally to catch errors before deploying
vercel build --prod

# Run test suite
npm test
```

### Step 2: Production Deploy
```bash
# Option A: Deploy directly to production
vercel --prod

# Option B: Promote an existing preview deployment
vercel promote https://my-app-git-main-team.vercel.app

# Option C: Deploy via API
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
      "sha": "abc123"
    }
  }'
```

### Step 3: Domain Configuration
```bash
# Add production domain
vercel domains add yourdomain.com

# Verify domain DNS
vercel domains inspect yourdomain.com

# DNS setup for apex domain (yourdomain.com):
# A record → 76.76.21.21
# AAAA record → (Vercel provides)

# DNS setup for subdomain (www.yourdomain.com):
# CNAME → cname.vercel-dns.com

# SSL is automatically provisioned after DNS verification
```

### Step 4: Post-Deploy Health Checks
```bash
# Verify production is responding
curl -sI https://yourdomain.com | head -5

# Test API endpoints
curl -s https://yourdomain.com/api/health | jq .

# Check SSL certificate
curl -vI https://yourdomain.com 2>&1 | grep "SSL certificate"

# Verify security headers
curl -sI https://yourdomain.com | grep -i "strict-transport\|x-frame\|x-content-type"

# Test from multiple regions (using Vercel's edge)
for region in iad1 sfo1 cdg1 hnd1; do
  echo "Region: $region"
  curl -s -H "x-vercel-ip-country: US" https://yourdomain.com/api/health
done
```

### Step 5: Instant Rollback Procedure
```bash
# If something goes wrong — instant rollback (no rebuild needed)
vercel rollback

# Or rollback to a specific deployment
vercel rollback dpl_xxxxxxxxxxxx

# Or via API
curl -X POST "https://api.vercel.com/v9/projects/my-app/promote" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deploymentId": "dpl_previous_good_deployment"}'

# Verify rollback succeeded
vercel ls --prod
curl -s https://yourdomain.com/api/health
```

### Step 6: Configure Function Regions and Limits
```json
// vercel.json — production optimization
{
  "regions": ["iad1"],
  "functions": {
    "api/**/*.ts": {
      "memory": 1024,
      "maxDuration": 30
    },
    "api/heavy-compute.ts": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

## Production Checklist

### Build & Deploy
- [ ] `npm run build` succeeds locally
- [ ] All tests passing
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] Preview deployment tested by team
- [ ] `vercel --prod` or promotion executed

### Environment Variables
- [ ] All required vars set for Production environment
- [ ] Secrets typed as `sensitive` (hidden in logs)
- [ ] No `NEXT_PUBLIC_` prefix on secrets
- [ ] Database URLs point to production instances

### Domain & SSL
- [ ] Custom domain added and DNS verified
- [ ] SSL certificate auto-provisioned and valid
- [ ] `www` subdomain redirects correctly
- [ ] HSTS header enabled

### Security
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)
- [ ] Preview deployment protection enabled
- [ ] API routes require authentication
- [ ] CORS configured for production origins only

### Performance
- [ ] Function regions set closest to your database
- [ ] `maxDuration` set appropriately per function
- [ ] Cache-Control headers configured
- [ ] Bundle size within budget (check with `vercel inspect`)
- [ ] Core Web Vitals in green (LCP < 2.5s, CLS < 0.1)

### Monitoring
- [ ] Error tracking configured (Sentry, Datadog, etc.)
- [ ] Vercel Analytics enabled in dashboard
- [ ] Runtime logs accessible
- [ ] Alert on error rate spikes

### Rollback
- [ ] Previous production deployment identified for rollback
- [ ] `vercel rollback` tested in staging
- [ ] Team knows rollback procedure

## Output
- Production deployment live on custom domain
- Health checks passing
- Security headers verified
- Rollback procedure documented and tested

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `DEPLOYMENT_BLOCKED` | Branch protection or deployment freeze | Check team settings in dashboard |
| SSL not provisioned | DNS not propagated | Wait for DNS propagation, verify records |
| Env var undefined | Not scoped to Production | Add via `vercel env add <key> production` |
| Function cold starts in prod | No warm-up traffic | Enable concurrency scaling or use edge functions |
| Rollback fails | Previous deployment expired | Redeploy from known good commit |

## Resources
- [Production Deployments](https://vercel.com/docs/deployments)
- [Instant Rollback](https://vercel.com/docs/instant-rollback)
- [Promoting Deployments](https://vercel.com/docs/deployments/promoting-a-deployment)
- [Custom Domains](https://vercel.com/docs/domains/working-with-domains)
- [Function Configuration](https://vercel.com/docs/functions/configuring-functions)

## Next Steps
For version upgrades, see `vercel-upgrade-migration`.
