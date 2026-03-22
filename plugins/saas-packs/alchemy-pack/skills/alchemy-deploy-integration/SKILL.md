---
name: alchemy-deploy-integration
description: |
  Deploy Alchemy-powered Web3 applications to Vercel, Cloud Run, and AWS.
  Use when deploying dApps with server-side Alchemy SDK access,
  configuring API key secrets, or setting up RPC proxy endpoints.
  Trigger: "deploy alchemy", "alchemy Vercel", "alchemy Cloud Run",
  "alchemy production deploy", "dApp deploy".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, deployment]
compatible-with: claude-code
---

# Alchemy Deploy Integration

## Overview

Deploy Alchemy-powered dApps with proper API key security. The API key must stay server-side — never ship it to the browser.

## Instructions

### Step 1: Vercel Deployment

```bash
# Add Alchemy API key as Vercel secret
vercel secrets add alchemy_api_key "your-api-key"
vercel link
vercel --prod
```

```json
// vercel.json
{
  "env": { "ALCHEMY_API_KEY": "@alchemy_api_key" },
  "functions": { "api/**/*.ts": { "maxDuration": 30 } }
}
```

```typescript
// api/balance/[address].ts — Vercel serverless function
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

export default async function handler(req: any, res: any) {
  const { address } = req.query;
  if (!/^0x[a-fA-F0-9]{40}$/.test(address)) {
    return res.status(400).json({ error: 'Invalid address' });
  }
  const balance = await alchemy.core.getBalance(address);
  res.json({ balance: balance.toString() });
}
```

### Step 2: Cloud Run Deployment

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/${PROJECT_ID}/alchemy-dapp
gcloud run deploy alchemy-dapp \
  --image gcr.io/${PROJECT_ID}/alchemy-dapp \
  --region us-central1 \
  --set-secrets=ALCHEMY_API_KEY=alchemy-api-key:latest \
  --allow-unauthenticated
```

### Step 3: Health Check

```typescript
// api/health.ts
import { Alchemy, Network } from 'alchemy-sdk';

export default async function handler(_req: any, res: any) {
  try {
    const alchemy = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ETH_MAINNET });
    const block = await alchemy.core.getBlockNumber();
    res.json({ status: 'healthy', latestBlock: block });
  } catch {
    res.status(503).json({ status: 'unhealthy' });
  }
}
```

## Output

- Vercel deployment with API key in server-side functions
- Cloud Run with GCP Secret Manager
- Health check endpoint verifying Alchemy connectivity

## Resources

- [Vercel Secrets](https://vercel.com/docs/concepts/projects/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Alchemy Docs](https://www.alchemy.com/docs)

## Next Steps

For webhook handling, see `alchemy-webhooks-events`.
