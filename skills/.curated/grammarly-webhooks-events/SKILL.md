---
name: grammarly-webhooks-events
description: 'Implement Grammarly webhook signature validation and event handling.

  Use when setting up webhook endpoints, implementing signature verification,

  or handling Grammarly event notifications securely.

  Trigger with phrases like "grammarly webhook", "grammarly events",

  "grammarly webhook signature", "handle grammarly events", "grammarly notifications".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Webhooks & Events

## Overview

Grammarly's current API is request/response based — there are no push webhooks. For async operations (plagiarism detection), you poll for results. Build your own event system around Grammarly API results.

## Instructions

### Step 1: Plagiarism Polling with Callback

```typescript
async function plagiarismWithCallback(
  text: string,
  token: string,
  onComplete: (result: any) => void
) {
  const createRes = await fetch('https://api.grammarly.com/ecosystem/api/v1/plagiarism', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  const { id } = await createRes.json();

  const poll = async () => {
    const res = await fetch(`https://api.grammarly.com/ecosystem/api/v1/plagiarism/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const result = await res.json();
    if (result.status === 'pending') { setTimeout(poll, 3000); return; }
    onComplete(result);
  };
  poll();
}
```

### Step 2: Build Event Bus for Score Results

```typescript
import { EventEmitter } from 'events';

const grammarlyEvents = new EventEmitter();

grammarlyEvents.on('score.completed', (data) => {
  if (data.overallScore < 60) console.warn('Low quality content detected');
});

grammarlyEvents.on('ai.detected', (data) => {
  if (data.score > 70) console.warn('Likely AI-generated content');
});
```

## Prerequisites

- A secret-manager webhook secret, event-origin allowlist, replay-window policy, and opaque event ledger.
- A sandbox receiver with fictional events plus a tested disable/rollback control for the consumer.

## Output

Return an event receipt with type, opaque ID, signature/timestamp result, idempotency outcome, queue state, retention/consent result, canary result, and rollback reference. Exclude payload text and signatures.

## Error Handling

Reject unknown origin, stale/replayed delivery, malformed payload, unknown destination, or non-idempotent retry. Quarantine the opaque event and disable the consumer if integrity or consent is uncertain.

## Examples

`type=check.completed; event=evt-opaque-9; signature=pass; replay=absent; enqueue=once; retention=none; rollback=consumer-disabled` proves the boundary.

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For performance, see `grammarly-performance-tuning`.
