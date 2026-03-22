---
name: webflow-security-basics
description: |
  Apply Webflow API security best practices — token management, scope least privilege,
  OAuth 2.0 secret rotation, webhook signature verification, and audit logging.
  Use when securing API tokens, implementing least privilege access,
  or auditing Webflow security configuration.
  Trigger with phrases like "webflow security", "webflow secrets",
  "secure webflow", "webflow API key security", "webflow token rotation".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Security Basics

## Overview

Security best practices for Webflow Data API v2 tokens, OAuth secrets, webhook
verification, and access control. Covers the full lifecycle from token creation
to rotation and revocation.

## Prerequisites

- Webflow developer account at `developers.webflow.com`
- Understanding of environment variables
- Secret management solution (vault, cloud secret manager, etc.)

## Instructions

### Step 1: Token Types and Selection

| Token Type | Scope | Best For |
|------------|-------|----------|
| **Workspace Token** | All sites in workspace | Internal tools, scripts |
| **Site Token** | Single site only | Single-site integrations |
| **OAuth Access Token** | User-authorized scopes | Public apps, marketplace apps |

**Rule: Never use a workspace token where a site token would suffice.**

### Step 2: Least Privilege Scopes

Only request scopes your integration actually needs:

| Operation | Minimum Scope |
|-----------|--------------|
| Read site info | `sites:read` |
| Publish site | `sites:write` |
| Read CMS content | `cms:read` |
| Create/update CMS items | `cms:write` |
| Read pages | `pages:read` |
| Read form submissions | `forms:read` |
| Read products/orders | `ecommerce:read` |
| Create products, fulfill orders | `ecommerce:write` |

```typescript
// Example: Read-only integration needs only these scopes
const READ_ONLY_SCOPES = "sites:read cms:read pages:read forms:read";

// CMS sync integration
const CMS_SYNC_SCOPES = "sites:read cms:read cms:write";

// Full ecommerce integration
const ECOMMERCE_SCOPES = "sites:read ecommerce:read ecommerce:write";
```

### Step 3: Secure Token Storage

```bash
# .gitignore — MANDATORY
.env
.env.local
.env.*.local
*.pem
*.key

# .env.local (never committed)
WEBFLOW_API_TOKEN=your-token-here
WEBFLOW_WEBHOOK_SECRET=your-webhook-secret
WEBFLOW_OAUTH_CLIENT_SECRET=your-oauth-secret
```

```typescript
// Load from environment, never hardcode
import { WebflowClient } from "webflow-api";

function createClient(): WebflowClient {
  const token = process.env.WEBFLOW_API_TOKEN;
  if (!token) {
    throw new Error(
      "WEBFLOW_API_TOKEN not set. " +
      "Generate at https://developers.webflow.com"
    );
  }
  return new WebflowClient({ accessToken: token });
}
```

### Step 4: Secret Rotation Procedure

```bash
# 1. Generate new token at developers.webflow.com
#    (old token remains valid until revoked)

# 2. Update secret in your deployment platform
# Vercel
vercel env rm WEBFLOW_API_TOKEN production
vercel env add WEBFLOW_API_TOKEN production

# Fly.io
fly secrets set WEBFLOW_API_TOKEN=new-token-here

# GCP Secret Manager
echo -n "new-token-here" | \
  gcloud secrets versions add webflow-api-token --data-file=-

# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id webflow/api-token \
  --secret-string "new-token-here"

# 3. Verify new token works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $NEW_TOKEN" \
  https://api.webflow.com/v2/sites

# 4. Revoke old token in Webflow dashboard
# 5. Monitor for 401 errors in logs
```

### Step 5: Environment-Specific Keys

```typescript
// Use different tokens per environment
const TOKEN_MAP: Record<string, string> = {
  development: "WEBFLOW_API_TOKEN_DEV",
  staging: "WEBFLOW_API_TOKEN_STAGING",
  production: "WEBFLOW_API_TOKEN_PROD",
};

function getToken(): string {
  const env = process.env.NODE_ENV || "development";
  const envVar = TOKEN_MAP[env] || TOKEN_MAP.development;
  const token = process.env[envVar];

  if (!token) throw new Error(`${envVar} not set for ${env} environment`);
  return token;
}
```

### Step 6: Webhook Signature Verification

Webflow webhooks include a signature header for request verification:

```typescript
import crypto from "crypto";

function verifyWebhookSignature(
  rawBody: Buffer | string,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) return false;

  const expectedSignature = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("hex");

  // Timing-safe comparison prevents timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false; // Length mismatch
  }
}

// Express middleware
import express from "express";

app.post(
  "/webhooks/webflow",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["x-webflow-signature"] as string;
    const secret = process.env.WEBFLOW_WEBHOOK_SECRET!;

    if (!verifyWebhookSignature(req.body, signature, secret)) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());
    // Process verified event...
    res.status(200).json({ received: true });
  }
);
```

### Step 7: Audit Logging

```typescript
interface WebflowAuditEntry {
  timestamp: string;
  operation: string;
  method: string;
  endpoint: string;
  statusCode: number;
  tokenType: "workspace" | "site" | "oauth";
  environment: string;
  durationMs: number;
}

function logApiCall(entry: WebflowAuditEntry): void {
  // Structured JSON log — ship to your logging platform
  console.log(JSON.stringify({
    level: entry.statusCode >= 400 ? "error" : "info",
    service: "webflow-integration",
    ...entry,
  }));
}
```

## Security Checklist

- [ ] API tokens stored in environment variables, never in code
- [ ] `.env` files in `.gitignore`
- [ ] Different tokens for dev/staging/production
- [ ] Minimal scopes per token (least privilege)
- [ ] Webhook signatures verified on every request
- [ ] Timing-safe comparison for signature checks
- [ ] Token rotation procedure documented and tested
- [ ] Audit logging enabled for all API calls
- [ ] No tokens in client-side code (tokens are server-side only)
- [ ] Git history scanned for accidentally committed tokens

## Output

- Secure token storage with environment isolation
- Least privilege scope selection
- Webhook signature verification
- Token rotation procedure
- Audit logging for compliance

## Error Handling

| Security Issue | Detection | Mitigation |
|---------------|-----------|------------|
| Token in git history | `git log -p \| grep WEBFLOW` | Revoke token immediately, rotate |
| Excessive scopes | Review at developers.webflow.com | Generate new token with minimal scopes |
| Missing webhook verification | No signature check in code | Add `verifyWebhookSignature()` |
| Token never rotated | No rotation log | Schedule quarterly rotation |

## Resources

- [Webflow Authentication](https://developers.webflow.com/data/reference/authentication)
- [Webflow Scopes](https://developers.webflow.com/data/reference/scopes)
- [OAuth Reference](https://developers.webflow.com/data/reference/oauth-app)

## Next Steps

For production deployment, see `webflow-prod-checklist`.
