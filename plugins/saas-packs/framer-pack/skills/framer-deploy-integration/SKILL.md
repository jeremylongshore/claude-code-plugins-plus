---
name: framer-deploy-integration
description: |
  Deploy Framer integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Framer-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy framer", "framer Vercel",
  "framer production deploy", "framer Cloud Run", "framer Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Deploy Integration

## Overview

Deploy Framer Server API integrations (CMS sync services, webhook handlers) to cloud platforms. Framer sites themselves are hosted by Framer — this covers deploying your backend services that interact with Framer.

## Instructions

### Step 1: Vercel Serverless (CMS Sync API)

```typescript
// api/sync-framer.ts — Vercel serverless function
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { framer } from 'framer-api';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).end();

  const client = await framer.connect({
    apiKey: process.env.FRAMER_API_KEY!,
    siteId: process.env.FRAMER_SITE_ID!,
  });

  const { items, collectionName } = req.body;
  const collections = await client.getCollections();
  const col = collections.find(c => c.name === collectionName);
  if (!col) return res.status(404).json({ error: 'Collection not found' });

  await col.setItems(items);
  await client.publish();
  res.json({ synced: items.length, published: true });
}
```

```bash
vercel env add FRAMER_API_KEY production
vercel env add FRAMER_SITE_ID production
vercel --prod
```

### Step 2: Fly.io (Long-Running Sync Service)

```bash
fly secrets set FRAMER_API_KEY=framer_sk_...
fly secrets set FRAMER_SITE_ID=abc123
fly deploy
```

### Step 3: Webhook Receiver for Content Updates

```typescript
// api/webhook-handler.ts — receive webhooks from your CMS, sync to Framer
export default async function handler(req, res) {
  const { event, data } = req.body;
  if (event === 'content.published') {
    const client = await framer.connect({ apiKey: process.env.FRAMER_API_KEY!, siteId: process.env.FRAMER_SITE_ID! });
    // Sync updated content to Framer CMS
    const col = (await client.getCollections()).find(c => c.name === 'Blog Posts');
    if (col) await col.setItems([{ fieldData: data }]);
    await client.publish();
  }
  res.json({ ok: true });
}
```

## Output

- Serverless CMS sync endpoint
- Webhook handler for content update automation
- Platform secrets configured

## Resources

- [Framer Server API](https://www.framer.com/developers/server-api-introduction)
- [Vercel Serverless](https://vercel.com/docs/functions)

## Next Steps

For webhook patterns, see `framer-webhooks-events`.
