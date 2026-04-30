---
name: openevidence-webhooks-events
description: 'Webhooks Events for OpenEvidence.

  Trigger: "openevidence webhooks events".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Webhooks & Events

## Overview
OpenEvidence delivers webhook notifications for clinical evidence retrieval workflows. Subscribe to events when queries complete, evidence bases are updated, new citations are added, or clinical reviews are flagged. Use these webhooks to keep clinical decision support systems current and trigger downstream audit workflows in real time.

## Webhook Registration
```typescript
const response = await fetch("https://api.openevidence.com/v1/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.OPENEVIDENCE_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/openevidence",
    events: ["query.completed", "evidence.updated", "citation.added", "review.flagged"],
    secret: process.env.OPENEVIDENCE_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyOpenEvidenceSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-openevidence-signature"] as string;
  const expected = crypto.createHmac("sha256", process.env.OPENEVIDENCE_WEBHOOK_SECRET!)
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

app.post("/webhooks/openevidence", express.raw({ type: "application/json" }), verifyOpenEvidenceSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "query.completed":
      deliverResults(event.data.query_id, event.data.evidence_count); break;
    case "evidence.updated":
      refreshClinicalCache(event.data.topic_id, event.data.revision); break;
    case "citation.added":
      indexCitation(event.data.citation_id, event.data.pubmed_id); break;
    case "review.flagged":
      escalateReview(event.data.review_id, event.data.flag_reason); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `query.completed` | `query_id`, `evidence_count`, `confidence` | Deliver clinical answers to requester |
| `evidence.updated` | `topic_id`, `revision`, `sources_changed` | Refresh cached evidence summaries |
| `citation.added` | `citation_id`, `pubmed_id`, `journal` | Index new literature into knowledge base |
| `review.flagged` | `review_id`, `flag_reason`, `severity` | Escalate flagged content for human review |
| `query.failed` | `query_id`, `error_code`, `retry_after` | Alert ops and queue retry |

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
| Signature mismatch | Secret rotation during deployment | Re-sync secret from OpenEvidence dashboard |
| Empty `evidence_count` | Query matched no indexed sources | Check query scope and topic coverage |
| Stale `pubmed_id` | Citation retracted after indexing | Subscribe to `citation.retracted` events |
| Review escalation loop | Automated re-flag on same content | Deduplicate by `review_id` with cooldown |

## Resources
- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps
See `openevidence-security-basics`.
