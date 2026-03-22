---
name: clay-webhooks-events
description: |
  Implement Clay webhook receivers and HTTP API column callbacks for real-time data flow.
  Use when setting up webhook endpoints, handling enrichment callbacks from Clay,
  or building event-driven integrations with Clay tables.
  Trigger with phrases like "clay webhook", "clay events", "clay callback",
  "handle clay data", "clay notifications", "clay HTTP API column".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, webhooks]

---
# Clay Webhooks & Events

## Overview

Clay's event-driven architecture has two webhook patterns: (1) **Inbound webhooks** -- you POST data into Clay tables via unique webhook URLs, and (2) **Outbound HTTP API columns** -- Clay POSTs enriched data to your endpoint after enrichment completes. This skill covers both patterns with production-ready handlers.

## Prerequisites

- Clay table with webhook source configured (for inbound)
- Clay table with HTTP API enrichment column (for outbound)
- HTTPS endpoint accessible from the internet
- Familiarity with Express.js or similar framework

## Instructions

### Step 1: Inbound Webhook -- Send Data into Clay

Every Clay table has a unique webhook URL. When you POST JSON to this URL, a new row appears in the table.

```typescript
// src/clay/inbound.ts — send data into Clay tables
class ClayInboundWebhook {
  constructor(
    private webhookUrl: string,
    private submissionCount: number = 0,
    private readonly LIMIT: number = 50_000,
  ) {}

  async sendRow(data: Record<string, unknown>): Promise<void> {
    if (this.submissionCount >= this.LIMIT) {
      throw new Error(`Webhook exhausted (${this.LIMIT} submissions). Create a new webhook in Clay.`);
    }

    const res = await fetch(this.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      throw new Error(`Clay webhook failed: ${res.status} ${res.statusText}`);
    }

    this.submissionCount++;
  }

  async sendBatch(rows: Record<string, unknown>[], delayMs = 200): Promise<{ sent: number; failed: number }> {
    let sent = 0, failed = 0;
    for (const row of rows) {
      try {
        await this.sendRow(row);
        sent++;
      } catch {
        failed++;
      }
      await new Promise(r => setTimeout(r, delayMs));
    }
    return { sent, failed };
  }
}

// Usage
const webhook = new ClayInboundWebhook(process.env.CLAY_WEBHOOK_URL!);
await webhook.sendRow({
  email: 'cto@acme.com',
  domain: 'acme.com',
  first_name: 'Jane',
  last_name: 'Doe',
  source: 'website-form',
});
```

### Step 2: Outbound Callback -- Receive Enriched Data from Clay

Clay's HTTP API enrichment column POSTs data to your endpoint after enrichment runs. Set up a handler:

```typescript
// src/clay/outbound-handler.ts — receive enriched data from Clay
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json({ limit: '1mb' }));

// Signature verification middleware
function verifyClaySignature(req: any, res: any, next: any) {
  const signature = req.headers['x-clay-signature'];
  const secret = process.env.CLAY_WEBHOOK_SECRET;

  if (secret && signature) {
    const expected = crypto.createHmac('sha256', secret)
      .update(JSON.stringify(req.body))
      .digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }
  next();
}

// Main callback endpoint
app.post('/api/clay/enriched', verifyClaySignature, async (req, res) => {
  // Respond 200 immediately — Clay expects fast response
  res.json({ received: true, timestamp: new Date().toISOString() });

  // Process enriched data async
  try {
    await processEnrichedLead(req.body);
  } catch (err) {
    console.error('Failed to process enriched lead:', err);
  }
});

interface EnrichedLead {
  email?: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  job_title?: string;
  employee_count?: number;
  industry?: string;
  linkedin_url?: string;
  icp_score?: number;
  personalized_opener?: string;
}

async function processEnrichedLead(lead: EnrichedLead): Promise<void> {
  // Route based on ICP score
  if (lead.icp_score && lead.icp_score >= 80 && lead.email) {
    await pushToOutreachSequence(lead);
  } else if (lead.icp_score && lead.icp_score >= 50) {
    await addToNurtureCampaign(lead);
  } else {
    console.log(`Low-score lead skipped: ${lead.email} (score: ${lead.icp_score})`);
  }
}
```

### Step 3: Configure the HTTP API Column in Clay

In your Clay table, add an HTTP API enrichment column:

1. **+ Add Column > HTTP API**
2. **Method**: POST
3. **URL**: `https://your-app.com/api/clay/enriched`
4. **Headers**:
   - `Content-Type: application/json`
   - `X-Clay-Signature: {{shared-secret-hash}}` (optional)
5. **Body** (map Clay columns to your schema):

```json
{
  "email": "{{Work Email}}",
  "first_name": "{{first_name}}",
  "last_name": "{{last_name}}",
  "company_name": "{{Company Name}}",
  "job_title": "{{Job Title}}",
  "employee_count": "{{Employee Count}}",
  "industry": "{{Industry}}",
  "linkedin_url": "{{LinkedIn URL}}",
  "icp_score": "{{ICP Score}}",
  "personalized_opener": "{{Personalized Opener}}"
}
```

6. **Conditional run**: `ISNOTEMPTY(Work Email) AND ICP Score >= 50`
7. **Auto-run on new rows**: ON

### Step 4: Idempotent Processing

Clay may retry failed HTTP API calls. Ensure idempotent handling:

```typescript
// src/clay/idempotency.ts
const processedSet = new Set<string>();

function getIdempotencyKey(lead: EnrichedLead): string {
  return crypto.createHash('sha256')
    .update(`${lead.email}:${lead.company_name}:${Date.now().toString().slice(0, -4)}`)
    .digest('hex');
}

async function processIdempotent(lead: EnrichedLead): Promise<boolean> {
  const key = getIdempotencyKey(lead);
  if (processedSet.has(key)) {
    console.log(`Duplicate callback skipped: ${lead.email}`);
    return false;
  }
  processedSet.add(key);
  await processEnrichedLead(lead);
  return true;
}
```

### Step 5: Integration with External Services

```typescript
// src/clay/integrations.ts — push enriched leads to downstream tools

// Zapier webhook trigger
async function triggerZapier(lead: EnrichedLead): Promise<void> {
  await fetch(process.env.ZAPIER_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lead),
  });
}

// Slack notification for high-value leads
async function notifySlack(lead: EnrichedLead): Promise<void> {
  if (!lead.icp_score || lead.icp_score < 90) return;

  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `Hot lead from Clay: ${lead.first_name} ${lead.last_name} (${lead.job_title}) at ${lead.company_name} - ICP Score: ${lead.icp_score}`,
    }),
  });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook returns 404 | URL expired or table deleted | Re-create webhook in Clay table |
| HTTP API column shows error | Your endpoint unreachable | Verify HTTPS URL is publicly accessible |
| Duplicate callbacks | Clay retried failed request | Implement idempotency (Step 4) |
| Webhook 50K limit hit | High volume usage | Create new webhook on same table |
| Callback timeout | Slow processing | Respond 200 immediately, process async |

## Resources

- [Clay University -- Webhook Integration Guide](https://university.clay.com/docs/webhook-integration-guide)
- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)
- [Clay University -- Using Clay as an API](https://www.clay.com/university/guide/using-clay-as-an-api)

## Next Steps

For performance optimization, see `clay-performance-tuning`.
