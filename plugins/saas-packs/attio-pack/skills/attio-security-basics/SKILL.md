---
name: attio-security-basics
description: |
  Secure Attio API integrations -- token scoping, secret management,
  scope auditing, webhook signature verification, and rotation procedures.
  Trigger: "attio security", "attio secrets", "secure attio",
  "attio API key security", "attio scopes", "attio token rotation".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Security Basics

## Overview

Attio access tokens never expire and have no scopes by default. This makes scoping, rotation, and secret management critical. This skill covers practical security controls for Attio REST API integrations.

## Token Properties

| Property | Value |
|----------|-------|
| Format | `sk_...` prefix |
| Expiration | Never (must be manually revoked) |
| Default scopes | None (you must explicitly add scopes) |
| Scope granularity | Per-resource read vs read-write |
| Auth method | `Authorization: Bearer <token>` header |

## Instructions

### Step 1: Apply Least-Privilege Scopes

Tokens should have only the scopes needed for their use case:

```
# Read-only analytics integration
object_configuration:read
record_permission:read

# CRM sync (needs write)
object_configuration:read
record_permission:read-write
list_entry:read-write

# Webhook receiver (just needs to verify, no API calls)
# No scopes needed -- webhook signature uses a separate secret

# Full admin (avoid in production)
object_configuration:read
record_permission:read-write
list_entry:read-write
note:read-write
task:read-write
user_management:read
webhook:read-write
```

### Step 2: Environment Variable Management

```bash
# .env.local (development -- git-ignored)
ATTIO_API_KEY=sk_dev_abc123

# .env.example (committed -- template for team)
ATTIO_API_KEY=sk_your_token_here
# ATTIO_WEBHOOK_SECRET=whsec_your_secret_here

# .gitignore (mandatory)
.env
.env.local
.env.*.local
```

**Platform-specific secrets management:**

```bash
# Vercel
vercel env add ATTIO_API_KEY production

# Fly.io
fly secrets set ATTIO_API_KEY=sk_prod_xyz

# Google Cloud (Secret Manager)
echo -n "sk_prod_xyz" | gcloud secrets create attio-api-key --data-file=-

# GitHub Actions
gh secret set ATTIO_API_KEY --body "sk_prod_xyz"

# AWS Systems Manager
aws ssm put-parameter --name /app/attio-api-key \
  --value "sk_prod_xyz" --type SecureString
```

### Step 3: Token Rotation Procedure

Attio tokens cannot be rotated in-place. You must create a new token and delete the old one.

```bash
# 1. Generate new token in Settings > Developers > Access tokens
#    Match the scopes of the old token exactly

# 2. Update the secret in your deployment platform
vercel env rm ATTIO_API_KEY production
vercel env add ATTIO_API_KEY production
# Enter new token value

# 3. Deploy with new token
vercel --prod

# 4. Verify the new token works
curl -s -o /dev/null -w "%{http_code}" \
  https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${NEW_TOKEN}"
# Should return 200

# 5. Delete old token in Attio dashboard
# Settings > Developers > Access tokens > Delete
```

### Step 4: Separate Tokens Per Environment

```typescript
// config/attio.ts
function getAttioToken(): string {
  const env = process.env.NODE_ENV || "development";
  const keyMap: Record<string, string> = {
    development: "ATTIO_API_KEY_DEV",
    staging: "ATTIO_API_KEY_STAGING",
    production: "ATTIO_API_KEY_PROD",
  };
  const key = process.env[keyMap[env] || "ATTIO_API_KEY"];
  if (!key) throw new Error(`Missing Attio token for ${env}`);
  return key;
}
```

### Step 5: Webhook Signature Verification

Attio webhooks include headers for signature verification:

```typescript
import crypto from "crypto";

function verifyAttioWebhook(
  rawBody: Buffer,
  signature: string,
  timestamp: string,
  secret: string
): boolean {
  // 1. Reject old timestamps (prevent replay attacks)
  const age = Date.now() - parseInt(timestamp) * 1000;
  if (age > 300_000) { // 5 minutes
    console.error("Webhook timestamp too old:", age, "ms");
    return false;
  }

  // 2. Compute expected signature
  const payload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  // 3. Timing-safe comparison (prevents timing attacks)
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false; // Different lengths
  }
}
```

### Step 6: Git Secret Scanning

```bash
# Pre-commit hook to catch Attio keys
# .git/hooks/pre-commit or via husky
#!/bin/bash
if git diff --cached --diff-filter=ACMR | grep -qE 'sk_[a-zA-Z0-9_]{20,}'; then
  echo "ERROR: Attio API key detected in staged changes"
  echo "Remove the key and use environment variables instead"
  exit 1
fi
```

### Step 7: Security Audit Checklist

```
[ ] API keys stored in environment variables, not code
[ ] .env files listed in .gitignore
[ ] Separate tokens per environment (dev/staging/prod)
[ ] Minimal scopes per token (least privilege)
[ ] Webhook signatures validated with timing-safe comparison
[ ] Replay attack protection (timestamp check) on webhooks
[ ] Pre-commit hook for secret scanning
[ ] Token rotation documented and scheduled
[ ] No tokens in logs, error messages, or client-side code
[ ] Audit trail: who has which tokens, when created
```

## Error Handling

| Security issue | Detection | Mitigation |
|---------------|-----------|------------|
| Token in git history | `git log -p --all -S 'sk_'` | Rotate immediately, use `git filter-repo` |
| Over-scoped token | Compare scopes to actual usage | Create new token with minimal scopes |
| Token shared across envs | Audit env configs | Create separate dev/staging/prod tokens |
| No webhook verification | Review webhook handler code | Implement signature check above |

## Resources

- [Attio Authentication Guide](https://docs.attio.com/rest-api/guides/authentication)
- [Attio Access Token Setup](https://attio.com/help/apps/other-apps/generating-an-api-key)
- [Attio Webhook Security](https://docs.attio.com/rest-api/guides/webhooks)

## Next Steps

For production deployment, see `attio-prod-checklist`.
