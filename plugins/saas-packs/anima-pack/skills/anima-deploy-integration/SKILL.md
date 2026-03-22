---
name: anima-deploy-integration
description: |
  Deploy Anima design-to-code service as a backend API endpoint.
  Use when building a design-to-code microservice, deploying Anima SDK
  as a serverless function, or creating an internal design tool API.
  Trigger: "deploy anima", "anima service deploy", "anima serverless".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, deployment]
compatible-with: claude-code
---

# Anima Deploy Integration

## Overview

Deploy the Anima SDK as a backend service. The SDK is server-side only, so deploy it behind an API endpoint that accepts Figma file/node references and returns generated code.

## Instructions

### Step 1: Express API Wrapper

```typescript
// src/server.ts
import express from 'express';
import { Anima } from '@animaapp/anima-sdk';

const app = express();
app.use(express.json());

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

app.post('/api/generate', async (req, res) => {
  const { fileKey, nodesId, settings } = req.body;

  if (!fileKey || !nodesId?.length) {
    return res.status(400).json({ error: 'fileKey and nodesId required' });
  }

  try {
    const { files } = await anima.generateCode({
      fileKey,
      figmaToken: process.env.FIGMA_TOKEN!,
      nodesId,
      settings: settings || { language: 'typescript', framework: 'react', styling: 'tailwind' },
    });
    res.json({ files, count: files.length });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/health', (_req, res) => res.json({ status: 'ok' }));
app.listen(3000, () => console.log('Anima service on :3000'));
```

### Step 2: Vercel Serverless Function

```typescript
// api/generate.ts
import { Anima } from '@animaapp/anima-sdk';

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') return res.status(405).end();

  const { fileKey, nodesId, settings } = req.body;
  const { files } = await anima.generateCode({
    fileKey, figmaToken: process.env.FIGMA_TOKEN!, nodesId,
    settings: settings || { language: 'typescript', framework: 'react', styling: 'tailwind' },
  });
  res.json({ files });
}
```

### Step 3: Deploy Commands

```bash
# Vercel
vercel secrets add anima_token "$ANIMA_TOKEN"
vercel secrets add figma_token "$FIGMA_TOKEN"
vercel --prod

# Cloud Run
gcloud run deploy anima-service \
  --source . \
  --set-secrets=ANIMA_TOKEN=anima-token:latest,FIGMA_TOKEN=figma-token:latest \
  --region us-central1 --allow-unauthenticated
```

## Output

- Express API wrapping Anima SDK for internal design tooling
- Vercel serverless function for lightweight deployment
- Cloud Run deployment with Secret Manager

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [Anima SDK Example Server](https://github.com/AnimaApp/anima-sdk)

## Next Steps

For webhook integration, see `anima-webhooks-events`.
