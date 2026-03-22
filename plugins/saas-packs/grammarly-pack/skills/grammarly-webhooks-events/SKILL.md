---
name: grammarly-webhooks-events
description: |
  Implement Grammarly webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Grammarly event notifications securely.
  Trigger with phrases like "grammarly webhook", "grammarly events",
  "grammarly webhook signature", "handle grammarly events", "grammarly notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
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

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For performance, see `grammarly-performance-tuning`.
