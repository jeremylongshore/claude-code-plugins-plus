---
name: glean-webhooks-events
description: 'Implement event-driven Glean indexing triggered by source system webhooks
  from

  GitHub, Confluence, Notion, and other content platforms.

  Trigger: "glean webhooks", "glean event indexing", "incremental glean index".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Webhooks & Events

## Overview
Glean uses an event-driven indexing model where source system webhooks trigger incremental updates to the Glean Indexing API. Instead of emitting its own webhooks, Glean receives document changes from platforms like GitHub, Confluence, and Notion. You can also monitor internal Glean events such as document indexing completion, permission changes, connector sync status, and search anomalies through the admin API.

## Webhook Registration
```typescript
// Register a source system webhook that pushes to Glean Indexing API
const response = await fetch("https://yourapp.com/admin/webhooks", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/glean-indexer",
    events: ["document.indexed", "permission.changed", "connector.synced", "search.anomaly"],
    secret: process.env.GLEAN_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyGleanSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-glean-signature"] as string;
  const expected = crypto.createHmac("sha256", process.env.GLEAN_WEBHOOK_SECRET!)
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

app.post("/webhooks/glean-indexer", express.raw({ type: "application/json" }), verifyGleanSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "document.indexed":
      confirmIndexStatus(event.data.datasource, event.data.doc_id); break;
    case "permission.changed":
      reindexPermissions(event.data.datasource, event.data.object_id); break;
    case "connector.synced":
      logSyncMetrics(event.data.connector_name, event.data.docs_processed); break;
    case "search.anomaly":
      alertOps(event.data.query_pattern, event.data.anomaly_type); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `document.indexed` | `datasource`, `doc_id`, `index_time_ms` | Confirm content is searchable |
| `permission.changed` | `datasource`, `object_id`, `new_acl` | Re-sync access controls |
| `connector.synced` | `connector_name`, `docs_processed`, `errors` | Monitor connector health |
| `search.anomaly` | `query_pattern`, `anomaly_type`, `severity` | Detect unusual search behavior |
| `document.deleted` | `datasource`, `doc_id`, `deleted_by` | Audit content removal |

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
| Index rejected | Document exceeds size limit | Chunk large documents before indexing |
| Permission denied | Stale OAuth token for connector | Refresh connector credentials in admin |
| Duplicate documents | Source sends create + update rapidly | Deduplicate by `doc_id` before indexing |
| Connector timeout | Source API rate limited | Implement exponential backoff in connector |

## Resources
- [Glean Indexing API](https://developers.glean.com/api/indexing-api/index-documents)

## Next Steps
See `glean-security-basics`.
