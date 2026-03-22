---
name: grammarly-deploy-integration
description: |
  Deploy Grammarly integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Grammarly-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy grammarly", "grammarly Vercel",
  "grammarly production deploy", "grammarly Cloud Run", "grammarly Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Deploy Integration

## Instructions

### Vercel Serverless — Writing Score API

```typescript
// api/score.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const { text } = req.body;
  if (!text || text.split(/\s+/).length < 30) return res.status(400).json({ error: 'Minimum 30 words' });

  // Get token via client credentials
  const tokenRes = await fetch('https://api.grammarly.com/ecosystem/api/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'client_credentials', client_id: process.env.GRAMMARLY_CLIENT_ID!, client_secret: process.env.GRAMMARLY_CLIENT_SECRET! }),
  });
  const { access_token } = await tokenRes.json();

  const scoreRes = await fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${access_token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  res.json(await scoreRes.json());
}
```

```bash
vercel env add GRAMMARLY_CLIENT_ID production
vercel env add GRAMMARLY_CLIENT_SECRET production
```

## Resources

- [Vercel](https://vercel.com/docs)

## Next Steps

For webhooks, see `grammarly-webhooks-events`.
