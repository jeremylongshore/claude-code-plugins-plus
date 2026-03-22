---
name: bamboohr-webhooks-events
description: |
  Implement BambooHR webhook endpoints with HMAC signature validation
  and employee change event handling. Covers global and permissioned webhooks.
  Use when setting up real-time employee notifications, implementing sync triggers,
  or handling BambooHR webhook payloads.
  Trigger with phrases like "bamboohr webhook", "bamboohr events",
  "bamboohr real-time sync", "bamboohr notifications", "bamboohr employee changes".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, webhooks]
compatible-with: claude-code
---

# BambooHR Webhooks & Events

## Overview

BambooHR supports two webhook types: **global webhooks** (configured in the BambooHR admin UI, subset of fields) and **permissioned webhooks** (created via API, access all fields the API key user can see). This skill covers creating, validating, and handling both types.

## Prerequisites

- BambooHR API key with webhook management permissions
- HTTPS endpoint accessible from the internet
- Webhook secret for HMAC-SHA256 signature verification

## Instructions

### Step 1: Understand Webhook Types

| Feature | Global Webhooks | Permissioned Webhooks |
|---------|----------------|----------------------|
| Setup | BambooHR admin UI | API (`POST /webhooks/`) |
| Field access | Subset of standard fields | All fields user can access |
| Auth | Shared secret | Per-webhook secret |
| Signature | SHA-256 HMAC | SHA-256 HMAC |
| Actions | Created, Updated, Deleted | Created, Updated, Deleted |

### Step 2: Create a Permissioned Webhook via API

```typescript
// POST /webhooks/ — register a new webhook
const webhook = await client.request<{
  id: number;
  name: string;
  privateKey: string; // Save this — used for HMAC verification
}>('POST', '/webhooks/', {
  name: 'Employee Sync Webhook',
  monitorFields: [
    'firstName', 'lastName', 'jobTitle', 'department',
    'division', 'location', 'workEmail', 'status',
    'supervisor', 'hireDate', 'terminationDate',
  ],
  postFields: {
    firstName: 'firstName',
    lastName: 'lastName',
    jobTitle: 'jobTitle',
    department: 'department',
    status: 'status',
    workEmail: 'workEmail',
  },
  url: 'https://your-app.example.com/webhooks/bamboohr',
  format: 'json',
  frequency: { every: 0 }, // 0 = immediate, or N = batch every N minutes
  limit: { enabled: false },
});

console.log(`Webhook ID: ${webhook.id}`);
console.log(`Private Key: ${webhook.privateKey}`);
// IMPORTANT: Store the privateKey securely — it's the HMAC secret
```

### Step 3: List and Manage Webhooks

```typescript
// GET /webhooks/ — list all webhooks for this API key
const webhooks = await client.request<any[]>('GET', '/webhooks/');
for (const wh of webhooks) {
  console.log(`${wh.id}: ${wh.name} -> ${wh.url} (${wh.status})`);
}

// GET /webhooks/{id}/ — get webhook details
const detail = await client.request<any>('GET', `/webhooks/${webhook.id}/`);

// GET /webhooks/{id}/log — get webhook delivery logs
const logs = await client.request<any[]>('GET', `/webhooks/${webhook.id}/log`);
for (const log of logs) {
  console.log(`${log.timestamp}: ${log.statusCode} (${log.employeeId})`);
}

// DELETE /webhooks/{id}/ — remove a webhook
await client.request('DELETE', `/webhooks/${webhook.id}/`);

// GET /webhooks/monitor_fields — see available fields to monitor
const fields = await client.request<any>('GET', '/webhooks/monitor_fields');
```

### Step 4: Signature Verification

BambooHR sends two headers: `X-BambooHR-Signature` (HMAC-SHA256 hex digest) and `X-BambooHR-Timestamp`.

```typescript
import crypto from 'crypto';

function verifyBambooHRWebhook(
  rawBody: Buffer | string,
  signature: string,
  timestamp: string,
  secret: string,
): boolean {
  // 1. Reject timestamps > 5 minutes old (replay protection)
  const age = Math.abs(Date.now() - parseInt(timestamp, 10) * 1000);
  if (age > 300_000) {
    console.error(`Webhook timestamp too old: ${age}ms`);
    return false;
  }

  // 2. Compute expected HMAC
  const payload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  // 3. Timing-safe comparison
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expected, 'hex'),
    );
  } catch {
    return false;
  }
}
```

### Step 5: Webhook Handler (Express.js)

```typescript
import express from 'express';

const app = express();

app.post('/webhooks/bamboohr',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const sig = req.headers['x-bamboohr-signature'] as string;
    const ts = req.headers['x-bamboohr-timestamp'] as string;

    if (!sig || !ts || !verifyBambooHRWebhook(req.body, sig, ts, process.env.BAMBOOHR_WEBHOOK_SECRET!)) {
      console.error('Webhook signature verification failed');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Parse the webhook payload
    const payload = JSON.parse(req.body.toString());
    // Respond immediately — process asynchronously
    res.status(200).json({ received: true });

    // Process each employee in the payload
    await processWebhookPayload(payload);
  },
);
```

### Step 6: Handle Webhook Payload

BambooHR webhook payloads contain employee data grouped by action type.

```typescript
interface BambooHRWebhookPayload {
  employees: {
    id: string;
    action: 'Created' | 'Updated' | 'Deleted';
    changedFields: string[];    // Which fields triggered this notification
    fields: Record<string, string>; // Current field values (from postFields config)
  }[];
}

async function processWebhookPayload(payload: BambooHRWebhookPayload): Promise<void> {
  for (const employee of payload.employees) {
    const { id, action, changedFields, fields } = employee;

    switch (action) {
      case 'Created':
        console.log(`New employee: ${fields.firstName} ${fields.lastName} (ID: ${id})`);
        await onEmployeeCreated(id, fields);
        break;

      case 'Updated':
        console.log(`Employee ${id} updated: ${changedFields.join(', ')}`);

        // Route to specific handlers based on what changed
        if (changedFields.includes('department') || changedFields.includes('jobTitle')) {
          await onPositionChanged(id, fields);
        }
        if (changedFields.includes('status')) {
          if (fields.status === 'Inactive') {
            await onEmployeeTerminated(id, fields);
          }
        }
        if (changedFields.includes('supervisor')) {
          await onManagerChanged(id, fields);
        }
        break;

      case 'Deleted':
        console.log(`Employee ${id} deleted`);
        await onEmployeeDeleted(id);
        break;
    }
  }
}

// Example handlers
async function onEmployeeCreated(id: string, fields: Record<string, string>) {
  // Provision accounts in external systems
  // e.g., create Slack account, set up email, assign training
}

async function onEmployeeTerminated(id: string, fields: Record<string, string>) {
  // Deprovisioning: disable accounts, revoke access, archive data
}

async function onPositionChanged(id: string, fields: Record<string, string>) {
  // Update org chart, Slack channels, access groups
}

async function onManagerChanged(id: string, fields: Record<string, string>) {
  // Update reporting hierarchy in downstream systems
}

async function onEmployeeDeleted(id: string) {
  // Remove from external systems
}
```

### Step 7: Idempotency (Prevent Duplicate Processing)

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function deduplicateWebhook(
  employeeId: string,
  action: string,
  changedFields: string[],
): Promise<boolean> {
  // Create a unique key for this specific change
  const changeKey = `bamboohr:webhook:${employeeId}:${action}:${changedFields.sort().join(',')}`;
  const wasSet = await redis.set(changeKey, '1', 'EX', 3600, 'NX'); // 1 hour TTL
  return wasSet === 'OK'; // true = first time, false = duplicate
}
```

### Step 8: Test Webhooks Locally

```bash
# 1. Expose local server with ngrok
ngrok http 3000
# Note the https:// URL

# 2. Create a test webhook pointing to your ngrok URL
# Use the API to create webhook with your ngrok URL

# 3. Or manually send a test payload
curl -X POST http://localhost:3000/webhooks/bamboohr \
  -H "Content-Type: application/json" \
  -H "X-BambooHR-Timestamp: $(date +%s)" \
  -H "X-BambooHR-Signature: test" \
  -d '{"employees": [{"id":"1","action":"Updated","changedFields":["department"],"fields":{"firstName":"Jane","department":"Engineering"}}]}'
```

## Output

- Webhook registered via BambooHR API with monitored fields
- HMAC-SHA256 signature verification on all incoming webhooks
- Event routing by action type (Created, Updated, Deleted)
- Field-specific change handlers (position, status, manager)
- Deduplication via Redis
- Local testing workflow with ngrok

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify `privateKey` from webhook creation |
| Empty `changedFields` | Created/Deleted action | Normal — only Updated includes changed fields |
| Missing fields in payload | Not in `postFields` config | Update webhook `postFields` configuration |
| Webhook not firing | Webhook disabled or URL unreachable | Check webhook status and logs via API |

## Enterprise Considerations

- **HTTPS required**: BambooHR only posts to HTTPS URLs
- **Retry behavior**: BambooHR retries failed deliveries; implement idempotency
- **Custom fields**: Permissioned webhooks can monitor custom fields (use field IDs from `/meta/fields/`)
- **Batch frequency**: Set `frequency.every` > 0 to batch multiple changes into fewer deliveries

## Resources

- [BambooHR Webhooks Guide](https://documentation.bamboohr.com/docs/webhooks)
- [BambooHR Global Webhooks](https://documentation.bamboohr.com/docs/global-webhooks)
- [BambooHR Permissioned Webhooks](https://documentation.bamboohr.com/docs/permissioned-webhooks)
- [BambooHR Webhook API Reference](https://documentation.bamboohr.com/reference/webhooks-1)

## Next Steps

For performance optimization, see `bamboohr-performance-tuning`.
