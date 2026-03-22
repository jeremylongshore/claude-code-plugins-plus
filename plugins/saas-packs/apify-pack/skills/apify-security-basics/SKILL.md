---
name: apify-security-basics
description: |
  Secure Apify API tokens, configure proxy access, and protect Actor data.
  Use when hardening API key management, setting up environment-specific tokens,
  or auditing Apify security configuration.
  Trigger: "apify security", "apify secrets", "secure apify token",
  "apify API key security", "rotate apify token".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Security Basics

## Overview

Security best practices for Apify API tokens, Actor data, proxy credentials, and webhook verification. Apify uses personal API tokens (prefixed `apify_api_`) for all authentication.

## Prerequisites

- Apify account with Console access
- Understanding of environment variables
- Access to your deployment platform's secrets management

## Token Architecture

Apify uses a single API token per user account for full API access. There is no scope-based permission system per token, so token security is critical.

| Token Type | Format | Where to Find |
|------------|--------|---------------|
| Personal API token | `apify_api_...` | Console > Settings > Integrations |
| Proxy password | Alphanumeric | Console > Proxy > Connection settings |

## Instructions

### Step 1: Secure Token Storage

```bash
# .env (NEVER commit — must be in .gitignore)
APIFY_TOKEN=apify_api_YOUR_TOKEN_HERE

# .gitignore — mandatory entries
.env
.env.local
.env.*.local
storage/   # Local Apify storage may contain scraped data
```

```typescript
// Validate token exists at startup
function requireToken(): string {
  const token = process.env.APIFY_TOKEN;
  if (!token) {
    throw new Error(
      'APIFY_TOKEN is required. Get yours at ' +
      'https://console.apify.com/account/integrations'
    );
  }
  if (!token.startsWith('apify_api_')) {
    console.warn('Warning: APIFY_TOKEN does not have expected prefix');
  }
  return token;
}
```

### Step 2: Per-Environment Token Isolation

Use separate Apify accounts (or at minimum separate tokens) per environment:

```bash
# Development — your personal account
APIFY_TOKEN=apify_api_dev_token

# Staging — shared team account (limited usage)
APIFY_TOKEN=apify_api_staging_token

# Production — production account (separate billing)
APIFY_TOKEN=apify_api_prod_token
```

Platform secrets management:
```bash
# GitHub Actions
gh secret set APIFY_TOKEN --body "apify_api_prod_token"

# Vercel
vercel env add APIFY_TOKEN production

# Google Cloud Secret Manager
echo -n "apify_api_prod_token" | \
  gcloud secrets create apify-token --data-file=-
```

### Step 3: Token Rotation Procedure

```bash
# 1. Generate new token in Console > Settings > Integrations
#    (old token remains valid until explicitly revoked)

# 2. Update in all environments
gh secret set APIFY_TOKEN --body "apify_api_NEW_TOKEN"

# 3. Verify new token works
curl -sf -H "Authorization: Bearer $NEW_TOKEN" \
  https://api.apify.com/v2/users/me | jq '.data.username'

# 4. Revoke old token in Console
#    Settings > Integrations > (regenerate invalidates old token)
```

### Step 4: Webhook Payload Verification

Apify webhooks include run data in the POST body. Verify the source:

```typescript
import crypto from 'crypto';
import { type Request, type Response } from 'express';

// Apify doesn't sign webhooks by default, but you can verify
// by checking that the run ID in the payload actually exists
async function verifyWebhookPayload(
  payload: { eventData: { actorRunId: string } },
  client: ApifyClient,
): Promise<boolean> {
  try {
    const run = await client.run(payload.eventData.actorRunId).get();
    return run !== null && run !== undefined;
  } catch {
    return false;
  }
}

// Alternatively, use a shared secret in your webhook URL
// https://your-server.com/webhook?secret=YOUR_WEBHOOK_SECRET
function verifyWebhookSecret(req: Request): boolean {
  const secret = req.query.secret as string;
  if (!secret || !process.env.APIFY_WEBHOOK_SECRET) return false;
  return crypto.timingSafeEqual(
    Buffer.from(secret),
    Buffer.from(process.env.APIFY_WEBHOOK_SECRET),
  );
}
```

### Step 5: Actor Data Security

```typescript
// Sanitize sensitive data before pushing to datasets
function sanitizeForDataset(item: Record<string, unknown>): Record<string, unknown> {
  const sensitiveFields = ['email', 'phone', 'password', 'ssn', 'creditCard'];
  const sanitized = { ...item };
  for (const field of sensitiveFields) {
    if (field in sanitized) {
      sanitized[field] = '***REDACTED***';
    }
  }
  return sanitized;
}

// Use named datasets with access control
// Only your account can access your datasets by default
// Public datasets require explicit sharing via API
```

### Step 6: Proxy Security

```typescript
// Never log or expose proxy URLs (they contain credentials)
const proxyConfig = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
  countryCode: 'US',
});

// DO NOT do this:
// console.log(await proxyConfig.newUrl()); // Leaks proxy password!

// Instead, log proxy group info only
console.log(`Using proxy group: ${proxyConfig.groups?.join(', ')}`);
```

## Security Checklist

- [ ] `APIFY_TOKEN` stored in environment variables (never hardcoded)
- [ ] `.env` and `storage/` in `.gitignore`
- [ ] Separate tokens for dev/staging/prod
- [ ] Token rotation schedule documented
- [ ] Webhook endpoints verify source
- [ ] Proxy URLs never logged
- [ ] Scraped PII redacted before storage
- [ ] Named datasets used for sensitive data (no public sharing)
- [ ] CI/CD secrets configured (not in repo)

## Leaked Token Response

If a token is exposed:

1. **Immediately** regenerate token in Console > Settings > Integrations
2. Check recent Actor runs for unauthorized usage
3. Review billing for unexpected charges
4. Rotate proxy password if exposed
5. Audit git history: `git log --all -p -- '*.env' '*.json' | grep apify_api_`

## Error Handling

| Issue | Detection | Mitigation |
|-------|-----------|------------|
| Token in git history | `git log -p \| grep apify_api_` | Rotate token, use BFG to clean |
| Unauthorized runs | Unexpected runs in Console | Rotate token immediately |
| Proxy password exposed | Credentials in logs | Regenerate proxy password |
| Data breach in dataset | PII in public dataset | Delete dataset, sanitize pipeline |

## Resources

- [Apify Account Security](https://docs.apify.com/platform/collaboration)
- [API Authentication](https://docs.apify.com/api/v2/getting-started)
- [Proxy Connection Settings](https://docs.apify.com/platform/proxy)

## Next Steps

For production deployment, see `apify-prod-checklist`.
