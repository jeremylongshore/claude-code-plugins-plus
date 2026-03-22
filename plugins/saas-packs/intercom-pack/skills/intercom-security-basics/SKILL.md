---
name: intercom-security-basics
description: |
  Apply Intercom security best practices for tokens, webhook verification, and scopes.
  Use when securing access tokens, implementing webhook signature validation,
  or configuring least-privilege OAuth scopes.
  Trigger with phrases like "intercom security", "intercom secrets",
  "secure intercom", "intercom webhook signature", "intercom token rotation".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Security Basics

## Overview

Security best practices for Intercom access tokens, webhook signature verification, Identity Verification (HMAC), and least-privilege OAuth scopes.

## Prerequisites

- Intercom access token or OAuth credentials
- Understanding of HMAC cryptographic signatures
- Access to Intercom Developer Hub

## Instructions

### Step 1: Secure Token Storage

```bash
# .env (NEVER commit to git)
INTERCOM_ACCESS_TOKEN=dG9rOmFiY2RlZmdoaQ==
INTERCOM_WEBHOOK_SECRET=your-webhook-signing-secret
INTERCOM_IDENTITY_SECRET=your-identity-verification-secret

# .gitignore (mandatory entries)
.env
.env.local
.env.*.local
```

Verify no tokens are committed:

```bash
# Scan git history for leaked tokens
git log --all -p | grep -i "INTERCOM_ACCESS_TOKEN\|dG9r" | head -5
# If found: rotate token immediately, then use git-filter-repo to remove
```

### Step 2: Webhook Signature Verification (X-Hub-Signature)

Intercom signs webhook notifications with HMAC-SHA1 using `X-Hub-Signature`. You must verify this on every incoming webhook.

```typescript
import crypto from "crypto";
import express from "express";

function verifyIntercomWebhook(
  payload: Buffer,
  signature: string,
  secret: string
): boolean {
  // Intercom uses X-Hub-Signature with HMAC-SHA1
  const expectedSignature = "sha1=" + crypto
    .createHmac("sha1", secret)
    .update(payload)
    .digest("hex");

  // Timing-safe comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

const app = express();

app.post(
  "/webhooks/intercom",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["x-hub-signature"] as string;

    if (!signature) {
      return res.status(401).json({ error: "Missing signature" });
    }

    if (!verifyIntercomWebhook(req.body, signature, process.env.INTERCOM_WEBHOOK_SECRET!)) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());
    // Process verified webhook...
    res.status(200).json({ received: true });
  }
);
```

### Step 3: Identity Verification (User Hash)

Intercom Identity Verification prevents impersonation by requiring an HMAC of the user's identifier.

```typescript
import crypto from "crypto";

// Server-side: generate user hash
function generateIntercomUserHash(userId: string): string {
  return crypto
    .createHmac("sha256", process.env.INTERCOM_IDENTITY_SECRET!)
    .update(userId)
    .digest("hex");
}

// Pass to frontend for Messenger initialization
app.get("/api/intercom-settings", (req, res) => {
  const userId = req.user.id;
  res.json({
    app_id: process.env.INTERCOM_APP_ID,
    user_id: userId,
    user_hash: generateIntercomUserHash(userId),
  });
});
```

### Step 4: Least-Privilege OAuth Scopes

Only request scopes your app actually needs:

| Use Case | Required Scopes |
|----------|----------------|
| Read contact data only | `Read contacts` |
| Manage conversations | `Read conversations`, `Write conversations` |
| Send messages | `Write messages` |
| Manage Help Center | `Read articles`, `Write articles` |
| Full CRM integration | `Read/write contacts`, `Read/write conversations`, `Read/write tags` |

### Step 5: Token Rotation Procedure

```bash
# 1. Generate new token in Developer Hub
#    Settings > Developer Hub > Your App > Authentication

# 2. Update in secret manager (examples)
# AWS
aws secretsmanager update-secret \
  --secret-id intercom/access-token \
  --secret-string "new_token_here"

# GCP
echo -n "new_token_here" | gcloud secrets versions add intercom-token --data-file=-

# Vault
vault kv put secret/intercom access_token="new_token_here"

# 3. Verify new token
curl -s https://api.intercom.io/me \
  -H "Authorization: Bearer $NEW_TOKEN" | jq '.type'
# Should return "admin"

# 4. Deploy updated config
# 5. Revoke old token in Developer Hub
```

## Security Checklist

- [ ] Access tokens stored in environment variables or secret manager
- [ ] `.env` files in `.gitignore`
- [ ] Different tokens for dev/staging/production workspaces
- [ ] Webhook signatures verified on every request (X-Hub-Signature)
- [ ] Identity Verification enabled (user_hash)
- [ ] OAuth scopes are minimal (least privilege)
- [ ] Token rotation procedure documented and tested
- [ ] Git history scanned for leaked credentials
- [ ] HTTPS enforced for all webhook endpoints

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Leaked token in git | `git log -p \| grep dG9r` | Rotate immediately, remove from history |
| Invalid webhook signature | 401 from verification | Check secret matches Developer Hub |
| Missing Identity Verification | Intercom dashboard warning | Implement user_hash on server |
| Excessive OAuth scopes | Scope audit | Remove unnecessary scopes |
| Token never rotated | Age tracking | Schedule quarterly rotation |

## Resources

- [Authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Webhook Notifications](https://developers.intercom.com/docs/webhooks/webhook-notifications)
- [Identity Verification](https://developers.intercom.com/installing-intercom/web/identity-verification)

## Next Steps

For production deployment, see `intercom-prod-checklist`.
