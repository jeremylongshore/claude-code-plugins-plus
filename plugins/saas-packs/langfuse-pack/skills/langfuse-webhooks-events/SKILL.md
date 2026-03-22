---
name: langfuse-webhooks-events
description: |
  Configure Langfuse webhooks for prompt change notifications and event-driven workflows.
  Use when setting up prompt change notifications, triggering CI/CD on prompt updates,
  or integrating Langfuse events with Slack and external systems.
  Trigger with phrases like "langfuse webhooks", "langfuse events",
  "langfuse notifications", "langfuse prompt webhook", "langfuse alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, webhooks]

---
# Langfuse Webhooks & Events

## Overview
Configure Langfuse webhooks to receive notifications on prompt version changes. Langfuse supports webhook events for prompt lifecycle: **Created**, **Updated** (labels/tags changed), and **Deleted**. Use webhooks to trigger CI/CD pipelines, sync prompts to external systems, or notify teams via Slack.

## Prerequisites
- Langfuse Cloud or self-hosted instance
- HTTPS endpoint to receive webhook POST requests
- Webhook secret for HMAC signature verification

## Instructions

### Step 1: Create Webhook Endpoint

```typescript
// app/api/webhooks/langfuse/route.ts (Next.js App Router)
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const WEBHOOK_SECRET = process.env.LANGFUSE_WEBHOOK_SECRET!;

interface LangfuseWebhookEvent {
  event: "prompt.created" | "prompt.updated" | "prompt.deleted";
  timestamp: string;
  data: {
    promptName: string;
    promptVersion: number;
    labels?: string[];
    projectId: string;
    [key: string]: any;
  };
}

// Verify HMAC SHA-256 signature
function verifySignature(payload: string, signature: string): boolean {
  const expected = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(payload)
    .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

export async function POST(request: NextRequest) {
  const payload = await request.text();
  const signature = request.headers.get("x-langfuse-signature");

  // Verify webhook authenticity
  if (!signature || !verifySignature(payload, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  const event: LangfuseWebhookEvent = JSON.parse(payload);
  console.log(`Langfuse webhook: ${event.event} - ${event.data.promptName}`);

  switch (event.event) {
    case "prompt.created":
      await handlePromptCreated(event.data);
      break;
    case "prompt.updated":
      await handlePromptUpdated(event.data);
      break;
    case "prompt.deleted":
      await handlePromptDeleted(event.data);
      break;
  }

  return NextResponse.json({ received: true });
}

async function handlePromptCreated(data: LangfuseWebhookEvent["data"]) {
  // Trigger CI/CD pipeline for new prompt version
  if (data.labels?.includes("production")) {
    await triggerPromptDeployPipeline(data.promptName, data.promptVersion);
  }

  await notifySlack({
    text: `New prompt version: *${data.promptName}* v${data.promptVersion}`,
    labels: data.labels,
  });
}

async function handlePromptUpdated(data: LangfuseWebhookEvent["data"]) {
  // Label change -- check if promoted to production
  if (data.labels?.includes("production")) {
    await notifySlack({
      text: `Prompt *${data.promptName}* v${data.promptVersion} promoted to production`,
    });
  }
}

async function handlePromptDeleted(data: LangfuseWebhookEvent["data"]) {
  await notifySlack({
    text: `Prompt *${data.promptName}* v${data.promptVersion} deleted`,
    level: "warning",
  });
}
```

### Step 2: Configure Webhook in Langfuse

1. Navigate to **Prompts > Create Automation > Webhook**
2. Enter your endpoint URL: `https://your-domain.com/api/webhooks/langfuse`
3. Select events to watch: Created, Updated, Deleted
4. Optionally filter to specific prompts
5. Generate and save the webhook secret
6. Click **Test** to verify connectivity

### Step 3: Slack Integration

```typescript
// lib/slack-notify.ts

async function notifySlack(params: {
  text: string;
  labels?: string[];
  level?: "info" | "warning";
}) {
  const color = params.level === "warning" ? "#ff9800" : "#36a64f";

  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      attachments: [
        {
          color,
          blocks: [
            {
              type: "section",
              text: { type: "mrkdwn", text: params.text },
            },
            ...(params.labels
              ? [
                  {
                    type: "context",
                    elements: [
                      {
                        type: "mrkdwn",
                        text: `Labels: ${params.labels.join(", ")}`,
                      },
                    ],
                  },
                ]
              : []),
          ],
        },
      ],
    }),
  });
}
```

### Step 4: Trigger CI/CD Pipeline on Prompt Changes

```typescript
// Trigger GitHub Actions workflow when production prompt changes
async function triggerPromptDeployPipeline(promptName: string, version: number) {
  await fetch(
    `https://api.github.com/repos/${process.env.GITHUB_REPO}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event_type: "prompt-updated",
        client_payload: { promptName, version },
      }),
    }
  );
}
```

```yaml
# .github/workflows/prompt-deploy.yml
name: Deploy Updated Prompt
on:
  repository_dispatch:
    types: [prompt-updated]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm" }
      - run: npm ci

      - name: Test updated prompt
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          echo "Testing prompt: ${{ github.event.client_payload.promptName }}"
          npx vitest run tests/ai/prompt-quality.test.ts
```

### Step 5: Webhook Reliability with Retry Queue

```typescript
// For production: queue webhook processing to return 200 fast
import { Queue, Worker } from "bullmq";

const webhookQueue = new Queue("langfuse-webhooks", {
  connection: { host: process.env.REDIS_HOST },
});

// In webhook handler -- enqueue and respond immediately
export async function POST(request: NextRequest) {
  const payload = await request.text();
  // ... verify signature ...

  await webhookQueue.add("process", JSON.parse(payload), {
    attempts: 3,
    backoff: { type: "exponential", delay: 1000 },
  });

  return NextResponse.json({ received: true }); // Return fast
}

// Worker processes asynchronously
const worker = new Worker(
  "langfuse-webhooks",
  async (job) => {
    const event = job.data as LangfuseWebhookEvent;
    // Process event...
  },
  { connection: { host: process.env.REDIS_HOST } }
);
```

## Webhook Event Reference

| Event | Trigger | Use Case |
|-------|---------|----------|
| `prompt.created` | New prompt version added | Run regression tests, notify team |
| `prompt.updated` | Labels or tags changed | Detect production promotions |
| `prompt.deleted` | Prompt version removed | Alert on accidental deletion |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature (401) | Wrong webhook secret | Re-copy secret from Langfuse settings |
| Missed events | Handler threw error | Queue events, return 200 immediately |
| Duplicate processing | Retry without idempotency | Dedupe by `event + timestamp + promptName` |
| Webhook timeout | Slow handler | Enqueue and process async |

## Resources
- [Langfuse Webhooks](https://langfuse.com/docs/prompt-management/features/webhooks-slack-integrations)
- [Prompt Version Webhooks Changelog](https://langfuse.com/changelog/2025-07-11-prompt-version-webhooks)
- [GitHub Integration](https://langfuse.com/docs/prompt-management/features/github-integration)
