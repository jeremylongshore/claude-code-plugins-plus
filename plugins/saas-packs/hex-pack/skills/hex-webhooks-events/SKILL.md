---
name: hex-webhooks-events
description: |
  Implement Hex webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Hex event notifications securely.
  Trigger with phrases like "hex webhook", "hex events",
  "hex webhook signature", "handle hex events", "hex notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Webhooks & Events

## Overview

Hex doesn't provide push webhooks. For event-driven integrations, poll run status or build your own notification system around run completions.

## Instructions

### Run Status Polling with Callback

```typescript
async function runWithCallback(
  client: HexClient,
  projectId: string,
  params: Record<string, any>,
  onComplete: (result: any) => void,
  onError: (error: Error) => void
) {
  try {
    const { runId } = await client.runProject(projectId, params);
    const poll = async () => {
      const status = await client.getRunStatus(projectId, runId);
      if (status.status === 'COMPLETED') { onComplete(status); return; }
      if (status.status === 'ERRORED' || status.status === 'KILLED') { onError(new Error(status.status)); return; }
      setTimeout(poll, 5000);
    };
    poll();
  } catch (err) { onError(err as Error); }
}
```

### Notify on Completion

```typescript
runWithCallback(client, 'project-id', { date: '2025-01-01' },
  (result) => {
    // Send Slack notification, email, etc.
    fetch(process.env.SLACK_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: `Hex project completed: ${result.runId}` }),
    });
  },
  (error) => console.error('Run failed:', error)
);
```

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-reference)
