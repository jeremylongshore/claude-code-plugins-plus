# Clay Webhooks & Events — Implementation Guide

## Webhook Endpoint with Signature Validation

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

## Event Router

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

## Enrichment Event Handlers

```typescript
async function handleEnrichmentComplete(payload: ClayWebhookPayload) {
  const { row_id, data } = payload;
  const enrichedCompany = data.company_enrichment;
  const linkedinData = data.linkedin_enrichment;

  console.log(`Enrichment complete for row ${row_id}`);

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

## Register Webhook via API

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

## Slack Notification Example

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
