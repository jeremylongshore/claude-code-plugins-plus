---
name: anima-rate-limits
description: |
  Implement rate limiting for Anima API code generation requests.
  Use when batching component generation, handling rate limit errors,
  or optimizing API throughput for large design systems.
  Trigger: "anima rate limit", "anima throttling", "anima batch generation".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, rate-limiting]
compatible-with: claude-code
---

# Anima Rate Limits

## Overview

Anima API has per-minute rate limits on code generation. Each `generateCode` call processes one Figma node through AI — it's compute-intensive and rate-limited accordingly.

## Rate Limit Tiers

| Tier | Generations/min | Concurrent | Notes |
|------|----------------|------------|-------|
| Partner (standard) | 10 | 2 | Most common |
| Enterprise | 30 | 5 | Custom agreement |

## Instructions

### Step 1: Throttled Generator with Bottleneck

```typescript
// src/anima/throttled-generator.ts
import Bottleneck from 'bottleneck';
import { Anima } from '@animaapp/anima-sdk';

const limiter = new Bottleneck({
  maxConcurrent: 2,
  minTime: 6000,          // 10 per minute = 1 every 6 seconds
  reservoir: 10,
  reservoirRefreshInterval: 60000,
  reservoirRefreshAmount: 10,
});

const anima = new Anima({ auth: { token: process.env.ANIMA_TOKEN! } });

async function throttledGenerate(params: any) {
  return limiter.schedule(() => anima.generateCode(params));
}

// Batch generate with automatic throttling
async function batchGenerate(nodeIds: string[], settings: any) {
  const results = [];
  for (const nodeId of nodeIds) {
    const result = await throttledGenerate({
      fileKey: process.env.FIGMA_FILE_KEY!,
      figmaToken: process.env.FIGMA_TOKEN!,
      nodesId: [nodeId],
      settings,
    });
    results.push({ nodeId, files: result.files });
    console.log(`Generated ${nodeId}: ${result.files.length} files`);
  }
  return results;
}

export { throttledGenerate, batchGenerate };
```

### Step 2: 429 Retry Handler

```typescript
async function generateWithRetry(anima: Anima, params: any, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await anima.generateCode(params);
    } catch (err: any) {
      if (err.response?.status !== 429 || attempt === maxRetries) throw err;
      const wait = Math.min(60000, 10000 * attempt); // Wait up to 60s
      console.log(`Rate limited — waiting ${wait / 1000}s`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
}
```

## Output

- Bottleneck-throttled code generation matching API limits
- Batch generator for design system-scale operations
- 429 retry handler with progressive backoff

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Bottleneck npm](https://www.npmjs.com/package/bottleneck)

## Next Steps

For security practices, see `anima-security-basics`.
