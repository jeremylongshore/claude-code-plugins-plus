# Apify Security — Full Implementation Reference

Deep, copy-paste implementations for each hardening step. The SKILL.md body
summarizes the workflow; drill in here for the complete code.

## Step 1: Secure Token Storage

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

## Step 2: Per-Environment Token Isolation

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

## Step 3: Token Rotation Procedure

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

## Step 4: Webhook Payload Verification

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

## Step 5: Actor Data Security

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

## Step 6: Proxy Security

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
