---
name: customerio-security-basics
description: |
  Apply Customer.io security best practices.
  Use when implementing secure credential storage, PII handling,
  webhook signature verification, or GDPR/CCPA compliance.
  Trigger: "customer.io security", "customer.io pii",
  "secure customer.io", "customer.io gdpr", "customer.io webhook verify".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, security, gdpr, compliance]

---
# Customer.io Security Basics

## Overview

Implement security best practices for Customer.io: secrets management for API credentials, PII sanitization before sending data, webhook signature verification (HMAC-SHA256), API key rotation, and GDPR/CCPA data deletion compliance.

## Prerequisites

- Customer.io account with admin access
- Understanding of your data classification (what is PII)
- Secrets management system (recommended for production)

## Instructions

### Step 1: Secure Credential Storage

```typescript
// lib/customerio-secrets.ts
// NEVER hardcode credentials — use environment variables or a secrets manager

// Option A: Environment variables (acceptable for most apps)
const siteId = process.env.CUSTOMERIO_SITE_ID;
const trackKey = process.env.CUSTOMERIO_TRACK_API_KEY;

// Option B: GCP Secret Manager (recommended for production)
import { SecretManagerServiceClient } from "@google-cloud/secret-manager";

const secretClient = new SecretManagerServiceClient();

async function getSecret(name: string): Promise<string> {
  const [version] = await secretClient.accessSecretVersion({
    name: `projects/my-project/secrets/${name}/versions/latest`,
  });
  return version.payload?.data?.toString() ?? "";
}

async function createCioClient() {
  const [siteId, trackKey] = await Promise.all([
    getSecret("customerio-site-id"),
    getSecret("customerio-track-api-key"),
  ]);

  return new TrackClient(siteId, trackKey, { region: RegionUS });
}
```

### Step 2: PII Sanitization

```typescript
// lib/customerio-sanitize.ts
// Sanitize user data BEFORE sending to Customer.io

const NEVER_SEND = new Set([
  "ssn", "social_security", "tax_id",
  "credit_card", "card_number", "cvv",
  "password", "password_hash",
  "bank_account", "routing_number",
]);

const HASH_FIELDS = new Set([
  "phone", "phone_number",
  "ip_address", "ip",
  "address", "street_address",
]);

import { createHash } from "crypto";

function hashValue(value: string): string {
  return createHash("sha256").update(value).digest("hex").substring(0, 16);
}

export function sanitizeAttributes(
  attrs: Record<string, any>
): Record<string, any> {
  const clean: Record<string, any> = {};

  for (const [key, value] of Object.entries(attrs)) {
    const lowerKey = key.toLowerCase();

    // Strip highly sensitive fields entirely
    if (NEVER_SEND.has(lowerKey)) continue;

    // Hash PII fields
    if (HASH_FIELDS.has(lowerKey) && typeof value === "string") {
      clean[`${key}_hash`] = hashValue(value);
      continue;
    }

    clean[key] = value;
  }

  return clean;
}

// Usage
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(siteId, trackKey, { region: RegionUS });

await cio.identify("user-123", sanitizeAttributes({
  email: "user@example.com",         // Kept (needed for email delivery)
  first_name: "Jane",                // Kept
  phone: "+1-555-0123",              // Hashed → phone_hash
  ssn: "123-45-6789",                // STRIPPED entirely
  plan: "pro",                       // Kept
}));
```

### Step 3: Webhook Signature Verification

Customer.io signs webhook payloads with HMAC-SHA256. Always verify before processing.

```typescript
// middleware/customerio-webhook.ts
import { createHmac, timingSafeEqual } from "crypto";
import { Request, Response, NextFunction } from "express";

const WEBHOOK_SECRET = process.env.CUSTOMERIO_WEBHOOK_SECRET!;

export function verifyCioWebhook(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const signature = req.headers["x-cio-signature"] as string;
  if (!signature) {
    res.status(401).json({ error: "Missing signature header" });
    return;
  }

  // req.body must be the raw buffer — configure Express accordingly
  const rawBody = (req as any).rawBody as Buffer;
  if (!rawBody) {
    res.status(500).json({ error: "Raw body not available" });
    return;
  }

  const expected = createHmac("sha256", WEBHOOK_SECRET)
    .update(rawBody)
    .digest("hex");

  const valid = timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );

  if (!valid) {
    res.status(401).json({ error: "Invalid signature" });
    return;
  }

  next();
}

// Express setup — raw body required for signature verification
import express from "express";
const app = express();

app.use("/webhooks/customerio", express.raw({ type: "application/json" }));
app.post("/webhooks/customerio", verifyCioWebhook, (req, res) => {
  const event = JSON.parse((req as any).rawBody.toString());
  // Process verified webhook event
  res.sendStatus(200);
});
```

### Step 4: API Key Rotation

```typescript
// scripts/rotate-cio-keys.ts
// Rotation procedure — zero downtime

async function rotateKeys() {
  console.log("Customer.io Key Rotation Procedure:");
  console.log("1. Go to Settings > Workspace Settings > API & Webhook Credentials");
  console.log("2. Click 'Regenerate' next to the key you want to rotate");
  console.log("3. Copy the NEW key");
  console.log("4. Update your secrets manager:");
  console.log("   - GCP: gcloud secrets versions add customerio-track-api-key --data-file=-");
  console.log("   - AWS: aws ssm put-parameter --name /cio/track-api-key --value NEW_KEY --overwrite");
  console.log("5. Deploy your application (or restart to pick up new secrets)");
  console.log("6. Verify: run the connectivity test script");
  console.log("7. The old key is immediately invalidated upon regeneration");
  console.log("");
  console.log("IMPORTANT: Regenerating a key IMMEDIATELY invalidates the old key.");
  console.log("Update secrets BEFORE regenerating, or plan for brief downtime.");
}
```

### Step 5: GDPR/CCPA Data Deletion

```typescript
// services/customerio-gdpr.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// GDPR Right to Erasure / CCPA Delete My Data
async function handleDeletionRequest(userId: string): Promise<void> {
  // 1. Suppress — stop all messaging immediately
  await cio.suppress(userId);
  console.log(`User ${userId} suppressed (no more messages)`);

  // 2. Destroy — remove profile and all data from Customer.io
  await cio.destroy(userId);
  console.log(`User ${userId} deleted from Customer.io`);

  // 3. Log the deletion for compliance audit trail
  console.log(`GDPR deletion completed for ${userId} at ${new Date().toISOString()}`);
}

// Bulk deletion (e.g., processing deletion requests from a queue)
async function bulkDelete(userIds: string[]): Promise<void> {
  for (const userId of userIds) {
    try {
      await handleDeletionRequest(userId);
    } catch (err: any) {
      // Log but continue — don't let one failure block others
      console.error(`Deletion failed for ${userId}: ${err.message}`);
    }
    // Respect rate limits
    await new Promise((r) => setTimeout(r, 100));
  }
}
```

## Security Checklist

- [ ] API keys stored in secrets manager (not `.env` in production)
- [ ] API key rotation schedule set (every 90 days)
- [ ] Webhook signatures verified (HMAC-SHA256 with `timingSafeEqual`)
- [ ] PII sanitized before sending to Customer.io
- [ ] Highly sensitive data (SSN, credit card) never sent
- [ ] GDPR deletion endpoint implemented (`suppress` + `destroy`)
- [ ] `.env` files in `.gitignore`
- [ ] Audit log for deletion requests
- [ ] Minimum necessary data principle applied

## Error Handling

| Issue | Solution |
|-------|----------|
| Credentials exposed in git | Rotate immediately, scan git history with `trufflehog` |
| PII accidentally sent | Delete user with `destroy()`, update sanitization rules |
| Webhook signature mismatch | Verify webhook secret matches Customer.io dashboard |
| Key rotation causes downtime | Update secrets manager BEFORE regenerating in dashboard |

## Resources

- [Customer.io Security](https://customer.io/security/)
- [API Credential Management](https://docs.customer.io/accounts-and-workspaces/managing-credentials/)
- [API Credential Rotation](https://customer.io/blog/api-credential-rotation/)
- [Suppression API](https://docs.customer.io/integrations/api/track/)

## Next Steps

After implementing security, proceed to `customerio-prod-checklist` for production readiness.
