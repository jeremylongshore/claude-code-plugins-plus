---
name: gamma-webhooks-events
description: |
  Handle Gamma webhooks and events for real-time updates.
  Use when implementing webhook receivers, processing events,
  or building real-time Gamma integrations.
  Trigger with phrases like "gamma webhooks", "gamma events",
  "gamma notifications", "gamma real-time", "gamma callbacks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, webhooks]

---
# Gamma Webhooks & Events

## Overview

Gamma's public API (v1.0) is generation-focused and does not expose a traditional webhook system at time of writing. Instead, use the **poll-based pattern** (GET `/v1.0/generations/{id}`) to detect completion. For event-driven architectures, wrap polling in a background worker that emits application-level events when generations complete or fail.

## Prerequisites

- Completed `gamma-sdk-patterns` setup
- Event bus or message queue (Bull, RabbitMQ, or EventEmitter)
- Understanding of the generate-poll-retrieve pattern

## Gamma Event Model (Application-Level)

Since Gamma does not push events, you create them by polling:

| Synthetic Event | Trigger Condition | Use Case |
|-----------------|-------------------|----------|
| `generation.started` | POST `/generations` returns `generationId` | Log, notify user |
| `generation.completed` | Poll returns `status: "completed"` | Download export, update DB |
| `generation.failed` | Poll returns `status: "failed"` | Alert, retry, notify user |
| `generation.timeout` | Poll exceeds max duration | Alert, escalate |

## Instructions

### Step 1: Event Emitter Pattern

```typescript
// src/gamma/events.ts
import { EventEmitter } from "events";
import { createGammaClient } from "./client";

export const gammaEvents = new EventEmitter();

export interface GenerationEvent {
  generationId: string;
  status: "started" | "completed" | "failed" | "timeout";
  gammaUrl?: string;
  exportUrl?: string;
  creditsUsed?: number;
  error?: string;
}

export async function generateWithEvents(
  content: string,
  options: { outputFormat?: string; exportAs?: string; themeId?: string } = {}
): Promise<GenerationEvent> {
  const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });

  // Start generation
  const { generationId } = await gamma.generate({
    content,
    outputFormat: options.outputFormat ?? "presentation",
    exportAs: options.exportAs,
    themeId: options.themeId,
  });

  gammaEvents.emit("generation", {
    generationId,
    status: "started",
  } as GenerationEvent);

  // Poll for completion
  const deadline = Date.now() + 180000; // 3 minute timeout
  while (Date.now() < deadline) {
    const result = await gamma.poll(generationId);

    if (result.status === "completed") {
      const event: GenerationEvent = {
        generationId,
        status: "completed",
        gammaUrl: result.gammaUrl,
        exportUrl: result.exportUrl,
        creditsUsed: result.creditsUsed,
      };
      gammaEvents.emit("generation", event);
      return event;
    }

    if (result.status === "failed") {
      const event: GenerationEvent = {
        generationId,
        status: "failed",
        error: "Generation failed",
      };
      gammaEvents.emit("generation", event);
      return event;
    }

    await new Promise((r) => setTimeout(r, 5000));
  }

  const timeoutEvent: GenerationEvent = {
    generationId,
    status: "timeout",
    error: "Poll timeout after 180s",
  };
  gammaEvents.emit("generation", timeoutEvent);
  return timeoutEvent;
}
```

### Step 2: Event Listeners

```typescript
// src/gamma/listeners.ts
import { gammaEvents, GenerationEvent } from "./events";

// Log all events
gammaEvents.on("generation", (event: GenerationEvent) => {
  console.log(`[Gamma] ${event.status}: ${event.generationId}`);
});

// Handle completed generations
gammaEvents.on("generation", async (event: GenerationEvent) => {
  if (event.status === "completed") {
    // Download export file
    if (event.exportUrl) {
      const res = await fetch(event.exportUrl);
      const buffer = Buffer.from(await res.arrayBuffer());
      // Save to S3, send to user, etc.
      console.log(`Downloaded export: ${buffer.length} bytes`);
    }

    // Update database
    await db.generations.update({
      where: { generationId: event.generationId },
      data: { status: "completed", gammaUrl: event.gammaUrl },
    });
  }
});

// Handle failures
gammaEvents.on("generation", async (event: GenerationEvent) => {
  if (event.status === "failed" || event.status === "timeout") {
    // Alert team
    await sendSlackAlert(`Gamma generation ${event.generationId} ${event.status}: ${event.error}`);
  }
});
```

### Step 3: Background Worker with Bull Queue

```typescript
// src/workers/gamma-worker.ts
import Bull from "bull";
import { createGammaClient } from "../gamma/client";

const generationQueue = new Bull("gamma-generations", process.env.REDIS_URL!);

// Producer: queue generation requests
export async function queueGeneration(content: string, options: any = {}) {
  return generationQueue.add(
    { content, ...options },
    { attempts: 2, backoff: { type: "exponential", delay: 10000 } }
  );
}

// Consumer: process in background
generationQueue.process(3, async (job) => {
  const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });
  const { content, outputFormat, exportAs } = job.data;

  const { generationId } = await gamma.generate({
    content,
    outputFormat: outputFormat ?? "presentation",
    exportAs,
  });

  // Poll until done
  const deadline = Date.now() + 180000;
  while (Date.now() < deadline) {
    await job.progress(Math.min(90, ((Date.now() - (deadline - 180000)) / 180000) * 100));
    const result = await gamma.poll(generationId);
    if (result.status === "completed") return result;
    if (result.status === "failed") throw new Error("Generation failed");
    await new Promise((r) => setTimeout(r, 5000));
  }
  throw new Error("Poll timeout");
});

generationQueue.on("completed", (job, result) => {
  console.log(`Generation completed: ${result.gammaUrl}`);
});

generationQueue.on("failed", (job, err) => {
  console.error(`Generation failed: ${err.message}`);
});
```

### Step 4: Webhook-Style HTTP Callback (DIY)

If you want true webhook-style push notifications for integrations:

```typescript
// src/gamma/callback.ts
// After generation completes, POST results to a configured URL

async function notifyCallback(callbackUrl: string, event: GenerationEvent) {
  await fetch(callbackUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event: `generation.${event.status}`,
      data: event,
      timestamp: new Date().toISOString(),
    }),
  });
}

// Usage: register a callback when starting a generation
const result = await generateWithEvents("My presentation content");
if (result.status === "completed") {
  await notifyCallback("https://your-app.com/hooks/gamma", result);
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Poll timeout | Generation taking too long | Increase timeout beyond 3 min for complex content |
| Missed completion | Poll interval too large | Use 5s interval (Gamma recommendation) |
| Duplicate processing | No idempotency check | Track processed generationIds in a Set or DB |
| Export URL expired | Downloaded too late | Download immediately on completion |

## Resources

- [Gamma API Reference](https://developers.gamma.app/reference/generate-a-gamma)
- [Poll Generation Status](https://developers.gamma.app/reference/get-a-gamma-generation)
- [Bull Queue Documentation](https://github.com/OptimalBits/bull)

## Next Steps

Proceed to `gamma-performance-tuning` for optimization.
