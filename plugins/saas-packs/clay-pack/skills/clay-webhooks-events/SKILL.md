---
name: clay-webhooks-events
description: |
  Implement Clay webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Clay event notifications securely.
  Trigger with phrases like "clay webhook", "clay events",
  "clay webhook signature", "handle clay events", "clay notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Webhooks & Events

## Overview
Handle Clay webhooks for real-time notifications when data enrichment completes, tables update, or workflows finish. Clay fires webhooks on enrichment lifecycle events so you can trigger downstream actions like CRM updates, Slack alerts, or pipeline syncs automatically.

## Prerequisites
- Clay account with API access and webhook configuration enabled
- HTTPS endpoint accessible from the internet
- Clay API key stored in `CLAY_API_KEY` environment variable
- Familiarity with Clay table and enrichment concepts

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `enrichment.completed` | Column enrichment finishes | Row data, enrichment results |
| `enrichment.failed` | Enrichment errors out | Row ID, error details |
| `table.row.created` | New row added to table | Full row data |
| `table.row.updated` | Row data changes | Changed fields, row ID |
| `table.export.completed` | Table export finishes | Export URL, row count |
| `workflow.completed` | Automated workflow ends | Workflow ID, results summary |

## Instructions

### Step 1: Configure Webhook Endpoint
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

app.post("/webhooks/clay",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-clay-signature"] as string;
    const secret = process.env.CLAY_WEBHOOK_SECRET!;

    const expected = crypto
      .createHmac("sha256", secret)
      .update(req.body)
      .digest("hex");

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());
    res.status(200).json({ received: true });
    await handleClayEvent(event);
  }
);
```

### Step 2: Route Events by Type
```typescript
interface ClayWebhookPayload {
  event: string;
  table_id: string;
  row_id?: string;
  data: Record<string, any>;
  timestamp: string;
}

async function handleClayEvent(payload: ClayWebhookPayload): Promise<void> {
  switch (payload.event) {
    case "enrichment.completed":
      await handleEnrichmentComplete(payload);
      break;
    case "enrichment.failed":
      await handleEnrichmentFailed(payload);
      break;
    case "table.row.created":
      await syncNewLeadToCRM(payload);
      break;
    case "table.export.completed":
      await processExportFile(payload);
      break;
    default:
      console.log(`Unhandled Clay event: ${payload.event}`);
  }
}
```

### Step 3: Handle Enrichment Results
```typescript
async function handleEnrichmentComplete(payload: ClayWebhookPayload) {
  const { row_id, data } = payload;
  const enrichedCompany = data.company_enrichment;
  const linkedinData = data.linkedin_enrichment;

  console.log(`Enrichment complete for row ${row_id}`);

  // Push enriched data to your CRM
  await crmClient.updateContact(row_id, {
    company: enrichedCompany?.name,
    companySize: enrichedCompany?.employee_count,
    linkedinUrl: linkedinData?.profile_url,
    title: linkedinData?.title,
  });
}

async function handleEnrichmentFailed(payload: ClayWebhookPayload) {
  const { row_id, data } = payload;
  console.error(`Enrichment failed for row ${row_id}: ${data.error}`);

  await retryQueue.add("clay-enrichment-retry", {
    rowId: row_id,
    tableId: payload.table_id,
    error: data.error,
  });
}
```

### Step 4: Register Webhook via Clay API
```bash
curl -X POST https://api.clay.com/v1/webhooks \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.yourapp.com/webhooks/clay",
    "events": ["enrichment.completed", "enrichment.failed", "table.row.created"],
    "table_id": "tbl_abc123"
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify secret in Clay dashboard settings |
| Missing enrichment data | Column not configured | Check enrichment column setup in table |
| Duplicate events | Retry delivery | Track `row_id + timestamp` for idempotency |
| Webhook timeout | Slow handler | Respond 200 immediately, process async |

## Examples

### Sync Enriched Leads to Slack
```typescript
async function syncNewLeadToCRM(payload: ClayWebhookPayload) {
  const { data } = payload;
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: `New enriched lead: ${data.full_name} at ${data.company}\nTitle: ${data.title}`,
    }),
  });
}
```

## Resources
- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Webhooks Guide](https://docs.clay.com/webhooks)

## Next Steps
For performance optimization, see `clay-performance-tuning`.
