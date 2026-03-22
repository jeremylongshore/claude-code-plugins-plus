---
name: brightdata-security-basics
description: |
  Apply Bright Data security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Bright Data security configuration.
  Trigger with phrases like "brightdata security", "brightdata secrets",
  "secure brightdata", "brightdata API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Security Basics

## Overview

Security best practices for Bright Data zone credentials, API tokens, and webhook delivery. Bright Data credentials include Customer ID, zone passwords, and API tokens — all must be protected.

## Prerequisites

- Bright Data zones configured
- Understanding of environment variables
- Access to Bright Data control panel

## Instructions

### Step 1: Credential Inventory

| Credential | Scope | Rotation | Storage |
|-----------|-------|----------|---------|
| Customer ID | Account-wide | Never changes | Can be in config |
| Zone Password | Per-zone | Rotate quarterly | Secrets vault only |
| API Token | Account-wide | Rotate quarterly | Secrets vault only |
| SSL Cert (`brd-ca.crt`) | Public | Auto-renewed | Can be in repo |

### Step 2: Environment Variable Security

```bash
# .env (NEVER commit)
BRIGHTDATA_CUSTOMER_ID=c_abc123
BRIGHTDATA_ZONE=web_unlocker1
BRIGHTDATA_ZONE_PASSWORD=z_pass_xyz
BRIGHTDATA_API_TOKEN=abc123def456

# .gitignore
.env
.env.local
.env.*.local

# .env.example (safe to commit — no real values)
BRIGHTDATA_CUSTOMER_ID=
BRIGHTDATA_ZONE=
BRIGHTDATA_ZONE_PASSWORD=
BRIGHTDATA_API_TOKEN=
```

### Step 3: Zone Isolation by Environment

Create separate zones per environment so staging credentials cannot access production proxy bandwidth:

```typescript
// config/brightdata.ts
const ZONE_MAP = {
  development: 'web_unlocker_dev',
  staging: 'web_unlocker_staging',
  production: 'web_unlocker_prod',
} as const;

export function getZone(): string {
  const env = process.env.NODE_ENV || 'development';
  return process.env.BRIGHTDATA_ZONE || ZONE_MAP[env] || ZONE_MAP.development;
}
```

### Step 4: Credential Rotation

```bash
# 1. Create new API token in Bright Data CP > Settings > API tokens
# 2. Update secrets in your deployment platform
# Vercel
vercel env rm BRIGHTDATA_API_TOKEN production
vercel env add BRIGHTDATA_API_TOKEN production

# AWS
aws secretsmanager update-secret --secret-id brightdata/api-token --secret-string "new_token"

# 3. Test new credentials
curl -H "Authorization: Bearer ${NEW_TOKEN}" \
  https://api.brightdata.com/zone/get_active_zones

# 4. Revoke old token in Bright Data CP
```

### Step 5: Git Secret Scanning

```bash
# Pre-commit hook to catch leaked credentials
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached | grep -iE '(BRIGHTDATA_ZONE_PASSWORD|BRIGHTDATA_API_TOKEN)=.{5,}'; then
  echo "ERROR: Bright Data credentials detected in staged changes"
  exit 1
fi
```

### Step 6: Webhook Delivery Security

When using webhook delivery for Web Scraper API results:

```typescript
// Validate webhook came from Bright Data
function validateWebhookSource(req: Request): boolean {
  // Bright Data sends from known IPs — check docs for current list
  // Also validate the Authorization header you configured
  const authHeader = req.headers.get('Authorization');
  return authHeader === `Bearer ${process.env.BRIGHTDATA_WEBHOOK_SECRET}`;
}
```

## Security Checklist

- [ ] Zone passwords in environment variables, never hardcoded
- [ ] `.env` files in `.gitignore`
- [ ] Separate zones per environment (dev/staging/prod)
- [ ] API tokens rotated quarterly
- [ ] Pre-commit hook blocks credential leaks
- [ ] Webhook endpoints validate Authorization header
- [ ] HTTPS-only for all proxy connections
- [ ] `brd-ca.crt` downloaded (public cert, safe in repo)

## Error Handling

| Issue | Detection | Mitigation |
|-------|-----------|------------|
| Leaked zone password | Git scanning, log monitoring | Rotate immediately in CP |
| Leaked API token | Secret scanning | Revoke in CP, create new token |
| Unauthorized zone usage | Billing alerts | Check zone activity logs |
| Proxy abuse | Unusual bandwidth spikes | Review zone usage in CP |

## Resources

- [Bright Data Security](https://docs.brightdata.com/general/account/security)
- [API Token Management](https://brightdata.com/cp/setting)
- [Zone Management](https://brightdata.com/cp/zones)

## Next Steps

For production deployment, see `brightdata-prod-checklist`.
