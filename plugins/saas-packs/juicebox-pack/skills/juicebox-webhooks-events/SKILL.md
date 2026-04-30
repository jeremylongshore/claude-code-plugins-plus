---
name: juicebox-webhooks-events
description: 'Handle Juicebox webhooks and events.

  Trigger: "juicebox webhooks", "juicebox events".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Webhooks & Events

## Overview
Juicebox delivers webhook notifications for AI-powered people search and analysis workflows. Subscribe to events for completed analyses, updated datasets, ready exports, and quota warnings to build automated pipelines that react to Juicebox intelligence in real time without polling the API.

## Webhook Registration
```typescript
const response = await fetch("https://api.juicebox.ai/v1/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.JUICEBOX_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/juicebox",
    events: ["analysis.completed", "dataset.updated", "export.ready", "quota.warning"],
    secret: process.env.JUICEBOX_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyJuiceboxSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-juicebox-signature"] as string;
  const expected = crypto.createHmac("sha256", process.env.JUICEBOX_WEBHOOK_SECRET!)
    .update(req.body).digest("hex");
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }
  next();
}
```

## Event Handler
```typescript
import express from "express";
const app = express();

app.post("/webhooks/juicebox", express.raw({ type: "application/json" }), verifyJuiceboxSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "analysis.completed":
      fetchResults(event.data.analysis_id, event.data.result_count); break;
    case "dataset.updated":
      refreshDashboard(event.data.dataset_id, event.data.records_added); break;
    case "export.ready":
      downloadExport(event.data.export_id, event.data.download_url); break;
    case "quota.warning":
      notifyAdmin(event.data.usage_percent, event.data.reset_date); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `analysis.completed` | `analysis_id`, `result_count`, `query` | Fetch and process search results |
| `dataset.updated` | `dataset_id`, `records_added`, `total_records` | Refresh downstream dashboards |
| `export.ready` | `export_id`, `download_url`, `format` | Auto-download CSV/JSON exports |
| `quota.warning` | `usage_percent`, `reset_date`, `plan_tier` | Alert admin before limit hit |
| `search.alert` | `alert_id`, `new_matches`, `criteria` | Notify on new candidate matches |

## Retry & Idempotency
```typescript
const processed = new Set<string>();

async function handleIdempotent(event: { id: string; type: string; data: any }) {
  if (processed.has(event.id)) return;
  await routeEvent(event);
  processed.add(event.id);
  if (processed.size > 10_000) {
    const entries = Array.from(processed);
    entries.slice(0, entries.length - 10_000).forEach((id) => processed.delete(id));
  }
}
```

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Signature mismatch | Secret rotated without updating handler | Re-fetch secret from Juicebox dashboard |
| Empty `result_count` | Analysis timed out | Check analysis status before processing |
| Export link expired | Download URL has 1-hour TTL | Fetch immediately on `export.ready` event |
| Quota exceeded | API calls after limit hit | Implement backoff until `reset_date` |

## Resources
- [Juicebox API Docs](https://docs.juicebox.ai)

## Next Steps
See `juicebox-security-basics`.
