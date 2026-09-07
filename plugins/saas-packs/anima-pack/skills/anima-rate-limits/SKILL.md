---
name: anima-rate-limits
description: 'Implement rate limiting for Anima API code generation requests.

  Use when batching component generation, handling rate limit errors,

  or optimizing API throughput for large design systems.

  Trigger: "anima rate limit", "anima throttling", "anima batch generation".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.4.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- design
- figma
- anima
- rate-limiting
compatibility: Designed for Claude Code
---
# Anima Rate Limits

## Overview

Anima API has per-minute rate limits on code generation. Each `generateCode` call processes one Figma node through AI — it's compute-intensive and rate-limited accordingly.

## Rate Limit Tiers

| Tier | Generations/min | Concurrent | Notes |
|------|----------------|------------|-------|
| Partner (standard) | 10 | 2 | Most common |
| Enterprise | 30 | 5 | Custom agreement |

## Prerequisites

- Confirm the account's current generation quota and concurrency contract before choosing `reservoir`, `reservoirRefreshAmount`, or `maxConcurrent`; treat the table above as a starting point, not authorization to exceed a plan.
- Store `ANIMA_TOKEN`, `FIGMA_TOKEN`, and `FIGMA_FILE_KEY` in the runtime secret manager or injected environment, and verify that the token has only the scopes required for the selected file. Never put tokens in source, fixtures, logs, generated receipts, or retry payloads.
- Define an explicit allowlist of Figma files and node IDs, a bounded batch size, a maximum retry budget, and an approved output directory. Use synthetic or sandbox designs for load tests and confirm that generated output contains no customer data before persisting it.
- Install the pinned SDK and Bottleneck versions, and decide whether a generation is safe to repeat. If the upstream operation is not idempotent, persist a redacted request fingerprint and resume only the failed node IDs.

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

## Error Handling

- For HTTP 429, honor a bounded `Retry-After` value when present; otherwise use exponential backoff with jitter and let the limiter continue to enforce the account-wide reservoir. Do not create a second uncoordinated retry loop around the same request.
- Do not retry 401/403 authentication or permission failures, invalid node/file parameters, or policy rejections. Stop the batch, report the node ID and redacted status, and repair credentials or scope before resuming.
- Retry only bounded transient 5xx and network failures. Cap attempts and total elapsed time, cancel queued work after the budget is exhausted, and preserve the successful results separately from failed node IDs so a resume cannot regenerate the whole batch accidentally.
- Treat timeout, process restart, and partial writes as ambiguous outcomes: check the request fingerprint or cache before resubmitting, write output atomically, and quarantine incomplete files. Logs and receipts may contain counts, status classes, and hashes, but not tokens, design contents, user identifiers, or generated source.
- Alert when the observed rate, queue depth, quota remaining, or failure ratio crosses the configured threshold. A human must approve any change to concurrency or quota settings; rollback means restoring the last known-good limiter configuration and draining queued work.

## Examples

For a sandbox batch, keep the work bounded and make the outcome auditable without exposing design data:

```typescript
const nodeIds = ['synthetic-card', 'synthetic-button'];
const receipt = {
  batchId: 'sandbox-2026-01-15-a',
  requested: nodeIds.length,
  succeeded: 0,
  failed: 0,
  contactsExported: 0,
};

for (const nodeId of nodeIds) {
  try {
    await throttledGenerate({ fileKey: process.env.FIGMA_FILE_KEY, nodesId: [nodeId], settings });
    receipt.succeeded++;
  } catch (error) {
    receipt.failed++;
    // Store only a redacted status and node fingerprint; never serialize `error` or source.
  }
}
console.log(JSON.stringify({ ...receipt, tokenPresent: Boolean(process.env.ANIMA_TOKEN) }));
```

An acceptable completion receipt is `requested=2; succeeded=2; failed=0; contacts_exported=0` with the sandbox ID and limiter settings recorded separately. A production batch should use the same controls, a reviewed allowlist, and an owner-approved change record before increasing concurrency.

## Output

- Bottleneck-throttled code generation matching API limits
- Batch generator for design system-scale operations
- 429 retry handler with progressive backoff

## Resources

- [Anima API Docs](https://docs.animaapp.com/docs/anima-api)
- [Bottleneck npm](https://www.npmjs.com/package/bottleneck)

## Next Steps

For security practices, see `anima-security-basics`.
