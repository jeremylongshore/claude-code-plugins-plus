---
name: instantly-security-basics
description: |
  Apply Instantly.ai security best practices for API keys, scopes, and access control.
  Use when securing API keys, implementing least-privilege access,
  or auditing Instantly workspace permissions.
  Trigger with phrases like "instantly security", "instantly api key safety",
  "instantly least privilege", "secure instantly", "instantly access control".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, security, access-control]

---
# Instantly Security Basics

## Overview
Secure your Instantly.ai integration with scoped API keys, least-privilege access, secret management, webhook validation, and audit logging. Instantly API v2 uses Bearer token auth with granular scope-based permissions.

## Prerequisites
- Instantly account with API access
- Understanding of environment variable management
- Access to Instantly dashboard Settings > Integrations

## Instructions

### Step 1: Least-Privilege API Key Scopes
Create separate API keys for different use cases with minimal required scopes.

```typescript
// Key scopes follow the pattern: resource:action
// resource = campaigns, accounts, leads, etc.
// action = read, update, all

// Read-only analytics dashboard
// Scopes needed: campaigns:read, accounts:read
const ANALYTICS_KEY_SCOPES = ["campaigns:read", "accounts:read"];

// Campaign automation bot
// Scopes needed: campaigns:all, leads:all
const AUTOMATION_KEY_SCOPES = ["campaigns:all", "leads:all"];

// Webhook-only integration
// Scopes needed: leads:read (to look up lead data on events)
const WEBHOOK_KEY_SCOPES = ["leads:read"];

// AVOID: all:all gives unrestricted access — dev/test only
```

| Use Case | Recommended Scopes | Risk Level |
|----------|-------------------|------------|
| Analytics dashboard | `campaigns:read`, `accounts:read` | Low |
| Lead import tool | `leads:update` | Medium |
| Campaign launcher | `campaigns:all`, `leads:all`, `accounts:read` | High |
| Full automation | `all:all` | Critical — dev only |
| Webhook handler | `leads:read` | Low |

### Step 2: Secret Management
```typescript
// NEVER hardcode API keys
// BAD:
const client = new InstantlyClient({ apiKey: "sk_live_abc123" });

// GOOD: environment variables
const client = new InstantlyClient({
  apiKey: process.env.INSTANTLY_API_KEY!,
});

// BETTER: secret manager integration
import { SecretManagerServiceClient } from "@google-cloud/secret-manager";

async function getApiKey(): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: "projects/my-project/secrets/instantly-api-key/versions/latest",
  });
  return version.payload?.data?.toString() || "";
}
```

```bash
# .gitignore — always exclude secrets
.env
.env.*
*.key
```

### Step 3: API Key Rotation
```typescript
// Instantly supports multiple API keys — rotate without downtime

async function rotateApiKey() {
  const oldKey = process.env.INSTANTLY_API_KEY;

  // 1. Create new API key via dashboard (Settings > Integrations > API)
  // 2. Update secret manager / env vars with new key
  // 3. Deploy with new key
  // 4. Verify new key works
  const client = new InstantlyClient({ apiKey: process.env.INSTANTLY_API_KEY_NEW! });
  await client.getCampaigns({ limit: 1 }); // test call

  // 5. Delete old key via API
  // GET /api/v2/api-keys to find the old key ID
  const keys = await client.request<Array<{ id: string; name: string }>>(
    "/api-keys"
  );
  const oldKeyEntry = keys.find((k) => k.name === "old-key-name");
  if (oldKeyEntry) {
    await client.request(`/api-keys/${oldKeyEntry.id}`, { method: "DELETE" });
    console.log("Old API key deleted");
  }
}

// API Key management endpoints:
// POST   /api/v2/api-keys        — Create new key (name, scopes)
// GET    /api/v2/api-keys        — List all keys
// DELETE /api/v2/api-keys/{id}   — Revoke a key
```

### Step 4: Webhook Security
```typescript
import express from "express";

const app = express();
app.use(express.json());

// Validate webhook requests
app.post("/webhooks/instantly", (req, res) => {
  // Option 1: Verify via custom header set during webhook creation
  const expectedSecret = process.env.INSTANTLY_WEBHOOK_SECRET;
  const receivedSecret = req.headers["x-webhook-secret"];

  if (expectedSecret && receivedSecret !== expectedSecret) {
    console.warn("Webhook auth failed: invalid secret");
    return res.status(401).json({ error: "Unauthorized" });
  }

  // Option 2: IP allowlisting (check Instantly's outbound IPs)
  // Option 3: Verify payload structure matches Instantly schema
  const { event_type, data } = req.body;
  if (!event_type || !data) {
    return res.status(400).json({ error: "Invalid payload" });
  }

  // Process immediately, return 200 fast (Instantly retries 3x in 30s)
  res.status(200).json({ received: true });

  // Async processing
  handleWebhookEvent(event_type, data).catch(console.error);
});

// When creating webhooks, add custom auth headers
async function createSecureWebhook(targetUrl: string) {
  return instantly("/webhooks", {
    method: "POST",
    body: JSON.stringify({
      name: "Secure CRM Sync",
      target_hook_url: targetUrl,
      event_type: "reply_received",
      headers: {
        "X-Webhook-Secret": process.env.INSTANTLY_WEBHOOK_SECRET,
        Authorization: `Basic ${Buffer.from("user:pass").toString("base64")}`,
      },
    }),
  });
}
```

### Step 5: Audit Logging
```typescript
// Instantly provides audit logs for workspace activity
async function checkAuditLogs() {
  const logs = await instantly<Array<{
    id: string;
    action: string;
    resource: string;
    timestamp_created: string;
    user: string;
  }>>("/audit-logs?limit=50");

  console.log("Recent Audit Events:");
  for (const log of logs) {
    console.log(`  ${log.timestamp_created} | ${log.action} | ${log.resource} | ${log.user}`);
  }
}
```

### Step 6: Workspace Member Permissions
```typescript
// Manage workspace members with role-based access
async function listWorkspaceMembers() {
  const members = await instantly<Array<{
    id: string;
    email: string;
    role: string;
  }>>("/workspace-members");

  for (const m of members) {
    console.log(`${m.email}: ${m.role}`);
  }
}

// Remove a member
async function removeMember(memberId: string) {
  await instantly(`/workspace-members/${memberId}`, { method: "DELETE" });
}
```

## Security Checklist
- [ ] API keys stored in environment variables or secret manager
- [ ] `.env` files listed in `.gitignore`
- [ ] Each integration has its own scoped API key
- [ ] No `all:all` keys in production
- [ ] Webhook endpoints validate authentication
- [ ] API key rotation schedule (quarterly recommended)
- [ ] Audit logs reviewed periodically
- [ ] Workspace members have minimum necessary roles
- [ ] Block list entries for competitor/internal domains

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401` after rotation | Old key still in use | Verify deployment picked up new key |
| `403` on scope-limited key | Missing required scope | Create new key with correct scopes |
| Webhook `401` | Secret mismatch | Check `headers` field in webhook config |
| Audit log empty | Plan doesn't include audit logs | Upgrade plan or check workspace settings |

## Resources
- [Instantly API Key Management](https://developer.instantly.ai/api/v2/apikey)
- [Instantly Webhook Docs](https://developer.instantly.ai/api/v2/webhook)
- [Audit Logs API](https://developer.instantly.ai/)

## Next Steps
For production readiness, see `instantly-prod-checklist`.
