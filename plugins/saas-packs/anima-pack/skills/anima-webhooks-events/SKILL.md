---
name: anima-webhooks-events
description: 'Use Figma webhooks to trigger automatic Anima code generation on design
  changes.

  Use when building event-driven design-to-code pipelines, auto-generating

  components when Figma files change, or integrating design updates into CI.

  Trigger: "anima webhook", "figma webhook", "anima auto-generate on change".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- webhooks
compatibility: Designed for Claude Code
---
# Anima Webhooks & Events

## Overview

Anima doesn't have its own webhooks, but you can use **Figma Webhooks** (v2 API) to detect design changes and trigger Anima code generation automatically. This creates an event-driven design-to-code pipeline.

## Prerequisites

- Team-level Figma webhook permission, a publicly reachable HTTPS endpoint,
  and a webhook passcode stored in a secret manager rather than source or
  request logs.
- An allowlist mapping approved file keys and component node IDs to their
  generated output directories and responsible owners.
- A durable event-id/version store, queue with retry and dead-letter handling,
  and a staging workspace containing synthetic design data.
- A rate-limit budget, replay/duplicate policy, and an explicit approval gate
  before generated code can be merged or deployed.

## Instructions

### Step 1: Register Figma Webhook

```bash
# Figma Webhooks API (requires team-level access)
curl -X POST "https://api.figma.com/v2/webhooks" \
  -H "X-Figma-Token: ${FIGMA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_VERSION_UPDATE",
    "team_id": "YOUR_TEAM_ID",
    "endpoint": "https://your-server.com/webhooks/figma",
    "passcode": "your-webhook-secret",
    "description": "Trigger Anima code generation on design changes"
  }'
```

### Step 2: Webhook Handler

```typescript
// src/webhooks/figma-handler.ts
import express from 'express';
import { Anima } from '@animaapp/anima-sdk';

const router = express.Router();
const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

interface FigmaWebhookEvent {
  event_type: 'FILE_VERSION_UPDATE' | 'FILE_UPDATE' | 'FILE_DELETE';
  file_key: string;
  file_name: string;
  triggered_by: { id: string; handle: string };
  timestamp: string;
  passcode: string;
}

router.post('/webhooks/figma', express.json(), async (req, res) => {
  const event = req.body as FigmaWebhookEvent;

  // Verify passcode
  if (event.passcode !== process.env.FIGMA_WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  // Only process file version updates
  if (event.event_type !== 'FILE_VERSION_UPDATE') {
    return res.status(200).json({ skipped: true });
  }

  console.log(`Design changed: ${event.file_name} by ${event.triggered_by.handle}`);

  // Trigger async generation — respond immediately
  regenerateComponents(event.file_key).catch(console.error);
  res.status(200).json({ accepted: true });
});

async function regenerateComponents(fileKey: string) {
  const COMPONENT_NODES = ['1:2', '3:4', '5:6']; // Your component node IDs

  for (const nodeId of COMPONENT_NODES) {
    try {
      const { files } = await anima.generateCode({
        fileKey,
        figmaToken: process.env.FIGMA_TOKEN!,
        nodesId: [nodeId],
        settings: { language: 'typescript', framework: 'react', styling: 'tailwind' },
      });
      console.log(`Regenerated node ${nodeId}: ${files.length} files`);
      await new Promise(r => setTimeout(r, 6000)); // Rate limit
    } catch (err) {
      console.error(`Failed to regenerate ${nodeId}:`, err);
    }
  }
}

export default router;
```

## Error Handling

| Failure | Required response |
|---------|-------------------|
| Passcode is missing or invalid | Return `401`, enqueue nothing, and record only a redacted rejection reason. |
| Event is malformed, duplicated, stale, or outside the file/node allowlist | Acknowledge safely where appropriate, discard the event, and retain a deduplicated audit receipt. |
| Generation or downstream quality checks fail | Retry with bounded backoff, then move the event to a dead-letter queue; do not open a merge or deploy automatically. |
| Figma or Anima rate limit is reached | Honor the provider response, apply queue backpressure, and preserve event order for the same file. |
| File is deleted or access is revoked | Disable further generation for that source and require owner confirmation before cleanup or re-registration. |

Verify the passcode before parsing or acting on design data, use an idempotency
key based on the webhook/version identity, and never log file contents,
triggerer handles, tokens, or full payloads. A failed regeneration must leave
the last known-good generated revision intact.

### Step 3: Figma Webhook Event Types

| Event Type | Trigger | Use Case |
|-----------|---------|----------|
| `FILE_VERSION_UPDATE` | New version saved | Regenerate components |
| `FILE_UPDATE` | File modified (real-time) | Too frequent — use version instead |
| `FILE_DELETE` | File deleted | Clean up generated code |
| `FILE_COMMENT` | Comment added | Notify design review channel |

## Output

- Figma webhook registration for design change detection
- Event handler triggering Anima code generation on file updates
- Rate-limited async regeneration pipeline

## Examples

Register a staging webhook with a managed passcode and an endpoint dedicated to
synthetic design fixtures:

```bash
curl -X POST "https://api.figma.com/v2/webhooks" \
  -H "X-Figma-Token: ${FIGMA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_VERSION_UPDATE",
    "team_id": "synthetic-team",
    "endpoint": "https://staging.example.invalid/webhooks/figma",
    "passcode": "'"${FIGMA_WEBHOOK_SECRET}"'",
    "description": "staging design sync"
  }'
```

Send one version-update fixture and confirm the endpoint returns immediately,
queues exactly one allowlisted generation, applies rate limiting, and produces
`contacts_exported=0` (or the equivalent no-external-write assertion). The
receipt should contain only the webhook/version identity, source allowlist
result, generation status, artifact digest, and cleanup/rollback result.

## Resources

- [Figma Webhooks API](https://www.figma.com/developers/api#webhooks-v2)
- [Anima API](https://docs.animaapp.com/docs/anima-api)

## Next Steps

For performance optimization, see `anima-performance-tuning`.
