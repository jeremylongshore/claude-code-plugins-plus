---
name: clay-security-basics
description: |
  Apply Clay security best practices for API keys, webhook secrets, and data access control.
  Use when securing Clay integrations, rotating API keys, auditing access,
  or implementing webhook authentication.
  Trigger with phrases like "clay security", "clay secrets", "secure clay",
  "clay API key security", "clay webhook security".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, security, audit]

---
# Clay Security Basics

## Overview

Security best practices for Clay integrations covering API key management, webhook endpoint security, provider credential isolation, and lead data protection. Clay handles sensitive PII (emails, phone numbers, LinkedIn profiles) at scale, making security critical.

## Prerequisites

- Clay account with admin access
- Understanding of environment variables and secrets management
- Access to deployment platform's secrets manager

## Instructions

### Step 1: Secure API Key Storage

```bash
# .env (NEVER commit to git)
CLAY_API_KEY=clay_ent_your_api_key_here
CLAY_WEBHOOK_URL=https://app.clay.com/api/v1/webhooks/your-id

# .gitignore — add these patterns
.env
.env.local
.env.*.local
*.key
```

For production, use your platform's secrets manager:

```bash
# GitHub Actions
gh secret set CLAY_API_KEY --body "clay_ent_your_key"

# Google Cloud Secret Manager
echo -n "clay_ent_your_key" | gcloud secrets create clay-api-key --data-file=-

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name clay/api-key \
  --secret-string "clay_ent_your_key"
```

### Step 2: Authenticate Incoming Webhook Callbacks

When Clay's HTTP API columns call your endpoint, validate the request origin:

```typescript
// src/middleware/clay-auth.ts
import crypto from 'crypto';

const CLAY_WEBHOOK_SECRET = process.env.CLAY_WEBHOOK_SECRET!;

function verifyClayCallback(
  payload: string,
  signature: string | undefined
): boolean {
  if (!signature || !CLAY_WEBHOOK_SECRET) return false;

  const expected = crypto
    .createHmac('sha256', CLAY_WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expected, 'hex')
  );
}

// Express middleware
function clayAuthMiddleware(req: any, res: any, next: any) {
  const signature = req.headers['x-clay-signature'] as string;
  const rawBody = JSON.stringify(req.body);

  if (!verifyClayCallback(rawBody, signature)) {
    console.warn('Rejected unauthorized Clay callback from', req.ip);
    return res.status(401).json({ error: 'Invalid signature' });
  }
  next();
}
```

### Step 3: Isolate Provider API Keys

Connect provider keys directly in Clay (Settings > Connections) rather than passing them through your application. This keeps provider credentials out of your codebase:

| Provider | Where to Store Key | Why |
|----------|-------------------|-----|
| Apollo | Clay Settings > Connections | 0 credits when using own key |
| Clearbit | Clay Settings > Connections | 0 credits when using own key |
| Hunter.io | Clay Settings > Connections | 0 credits when using own key |
| HubSpot | Clay Settings > Connections | CRM sync uses Clay's OAuth |
| Salesforce | Clay Settings > Connections | CRM sync uses Clay's OAuth |

### Step 4: API Key Rotation Procedure

```bash
# 1. Generate new key in Clay Settings > API
# 2. Update all integrations with new key
# 3. Test connectivity
curl -s -X POST "https://api.clay.com/v1/people/enrich" \
  -H "Authorization: Bearer $NEW_CLAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' | jq .status

# 4. Once confirmed working, revoke old key in Clay dashboard
# 5. Update deployment secrets
gh secret set CLAY_API_KEY --body "$NEW_CLAY_API_KEY"
```

### Step 5: Protect Enriched Lead Data

```typescript
// src/clay/data-protection.ts
const PII_FIELDS = ['email', 'phone', 'personal_email', 'home_address', 'linkedin_url'];

/** Strip PII from enriched data before logging or analytics */
function redactPII(row: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...row };
  for (const field of PII_FIELDS) {
    if (field in redacted) {
      redacted[field] = '[REDACTED]';
    }
  }
  return redacted;
}

/** Hash email for deduplication without storing plaintext */
function hashEmail(email: string): string {
  return crypto.createHash('sha256').update(email.toLowerCase().trim()).digest('hex');
}

// Usage: log enriched data safely
console.log('Enriched:', redactPII(enrichedRow));
```

### Step 6: Security Checklist

- [ ] API keys stored in environment variables or secrets manager
- [ ] `.env` files in `.gitignore`
- [ ] Webhook callback endpoints validate request signatures
- [ ] Provider API keys connected in Clay UI (not in application code)
- [ ] API key rotation procedure documented and tested
- [ ] Enriched PII data redacted in application logs
- [ ] Clay workspace uses separate API keys per integration
- [ ] Least privilege: viewers can't run enrichments or export data
- [ ] No hardcoded Clay URLs or keys in source code
- [ ] git-secrets or similar scanning enabled in CI

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| API key in git history | `git log -p --all -S 'clay_ent_'` | Rotate key immediately, use BFG to scrub |
| Unauthorized webhook calls | Missing signature validation | Add HMAC verification middleware |
| Over-permissioned users | Viewers running enrichments | Audit roles in Settings > Members |
| PII in application logs | grep logs for email patterns | Add PII redaction to log pipeline |

## Resources

- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

For production deployment, see `clay-prod-checklist`.
