---
name: anima-webhooks-events
description: |
  Use Figma webhooks to trigger automatic Anima code generation on design changes.
  Use when building event-driven design-to-code pipelines, auto-generating
  components when Figma files change, or integrating design updates into CI.
  Trigger: "anima webhook", "figma webhook", "anima auto-generate on change".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, webhooks]
compatible-with: claude-code
---

# Anima Webhooks & Events

## Overview

Anima doesn't have its own webhooks, but you can use **Figma Webhooks** (v2 API) to detect design changes and trigger Anima code generation automatically. This creates an event-driven design-to-code pipeline.

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

## Resources

- [Figma Webhooks API](https://www.figma.com/developers/api#webhooks-v2)
- [Anima API](https://docs.animaapp.com/docs/anima-api)

## Next Steps

For performance optimization, see `anima-performance-tuning`.
