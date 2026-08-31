---
name: alchemy-deploy-integration
description: 'Deploy Alchemy-powered Web3 applications to Vercel, Cloud Run, and AWS.

  Use when deploying dApps with server-side Alchemy SDK access,

  configuring API key secrets, or setting up RPC proxy endpoints.

  Trigger: "deploy alchemy", "alchemy Vercel", "alchemy Cloud Run",

  "alchemy production deploy", "dApp deploy".

  '
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(docker:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- blockchain
- web3
- alchemy
- deployment
compatibility: Designed for Claude Code
---
# Alchemy Deploy Integration

## Overview

Deploy Alchemy-powered dApps with proper API key security. The API key must stay server-side — never ship it to the browser.

## Prerequisites

- A server-side deployment target with a managed secret store and a scoped
  Alchemy key that is distinct from local development credentials.
- Input validation, rate limiting, and logging rules for any public RPC proxy
  endpoint so arbitrary callers cannot turn it into an account-exhaustion path.
- A tested rollback target and authenticated operational health check that does
  not reveal credentials, internal configuration, or user activity.

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

## Examples

Deploy a staging serverless balance endpoint with the API key injected only by
the platform secret binding, then call it with a public test address. Confirm
that invalid addresses return `400`, valid requests return only the intended
balance field, and neither response nor build artifact contains key material.
Record the deployment revision and authenticated health result as the release
receipt. If the secret binding, server-side boundary, or health check fails,
roll traffic back to the prior revision and correct the deployment settings;
never work around the failure by embedding a key in client code or source.

## Error Handling

| Failure | Response |
|---------|----------|
| Secret is unavailable at runtime | Fail closed, verify the managed binding, and do not substitute a plaintext fallback. |
| Public endpoint receives malformed input | Return a bounded client error before invoking the provider. |
| Provider health check fails | Mark the service degraded, alert the operator, and preserve the previous healthy revision. |
| API key appears in output or artifact | Revoke it, remove the exposure, audit logs/builds, and redeploy with a replacement. |

## Resources

- [Vercel Secrets](https://vercel.com/docs/concepts/projects/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Alchemy Docs](https://www.alchemy.com/docs)

## Next Steps

For webhook handling, see `alchemy-webhooks-events`.
