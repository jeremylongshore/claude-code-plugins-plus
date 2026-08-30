---
name: lindy-local-dev-loop
description: 'Set up local development workflow for testing Lindy AI agent integrations.

  Use when building webhook receivers, testing agent callbacks,

  or iterating on Lindy-connected applications locally.

  Trigger with phrases like "lindy local dev", "lindy development",

  "test lindy locally", "lindy webhook local".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(npx:*)
version: 1.19.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- testing
- workflow
compatibility: Designed for Claude Code
---
# Lindy Local Dev Loop

## Overview

Lindy agents run on Lindy's managed infrastructure — you do not run agents locally.
Local development focuses on building and testing the **webhook receivers**, **callback
handlers**, and **application code** that Lindy agents interact with. Use ngrok or
similar tunnels to expose local endpoints for Lindy webhook triggers.

## Prerequisites

- Node.js 18+ or Python 3.10+
- ngrok or Cloudflare Tunnel for HTTPS tunneling
- Lindy account with at least one agent configured
- Completed `lindy-install-auth` setup

## Instructions

### Step 1: Create Webhook Receiver

```typescript
// server.ts — Express webhook receiver for Lindy callbacks
import express from 'express';
import dotenv from 'dotenv';
dotenv.config();

const app = express();
app.use(express.json());

const CALLBACK_SECRET = process.env.LINDY_CALLBACK_SECRET;
if (!CALLBACK_SECRET) {
  throw new Error('LINDY_CALLBACK_SECRET is required');
}

// Verify Lindy webhook authenticity
function verifyWebhook(req: express.Request): boolean {
  const auth = req.headers.authorization;
  return auth === `Bearer ${CALLBACK_SECRET}`;
}

// Receive Lindy agent callbacks
app.post('/lindy/callback', (req, res) => {
  if (!verifyWebhook(req)) {
    console.error('Unauthorized webhook attempt');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Correlate the callback without logging its result or customer payload.
  const { taskId, status } = req.body;
  console.log(`Task ${taskId}: ${status}`);

  res.json({ received: true });
});

// Health check for Lindy to verify endpoint
app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.listen(3000, () => console.log('Webhook receiver running on :3000'));
```

### Step 2: Expose Local Server via Tunnel

```bash
# Install an HTTPS tunnel with your approved package-management policy, then run it.
ngrok http 3000

# Output: https://abc123.ngrok.io -> http://localhost:3000
# Use this URL in Lindy webhook configuration
```

### Step 3: Configure Lindy Agent to Call Your Endpoint

In the Lindy dashboard, add an **HTTP Request** action to your agent:

- **Method**: POST
- **URL**: `https://abc123.ngrok.io/lindy/callback`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <development callback secret>`
- **Body** (AI Prompt mode):

  ```
  Send the task result as JSON with fields: taskId, result, status
  ```

The tunnel is the destination of the agent's **HTTP Request action**. A webhook
trigger is the opposite direction: it uses the Lindy-hosted trigger URL to start
the agent and must not be replaced with the tunnel URL.

### Step 4: Create Test Harness

```typescript
// test-trigger.ts — Fire a test webhook to your Lindy agent
import fetch from 'node-fetch';

async function triggerAgent() {
  const rawWebhookUrl = process.env.LINDY_WEBHOOK_URL;
  const TRIGGER_SECRET = process.env.LINDY_TRIGGER_SECRET;
  if (!rawWebhookUrl || !TRIGGER_SECRET) {
    throw new Error('LINDY_WEBHOOK_URL and LINDY_TRIGGER_SECRET are required');
  }

  const webhookUrl = new URL(rawWebhookUrl);
  if (webhookUrl.protocol !== 'https:' || webhookUrl.hostname !== 'public.lindy.ai') {
    throw new Error('Refusing to send LINDY_TRIGGER_SECRET outside public.lindy.ai');
  }

  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TRIGGER_SECRET}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      action: 'test',
      data: { message: 'Hello from local dev', timestamp: new Date().toISOString() },
    }),
  });

  console.log(`Status: ${response.status}`);
  console.log(`Response: ${await response.text()}`);
}

triggerAgent();
```

### Step 5: Watch Mode Development

```json
// package.json scripts
{
  "scripts": {
    "dev": "tsx watch server.ts",
    "test:trigger": "tsx test-trigger.ts",
    "tunnel": "ngrok http 3000"
  }
}
```

```bash
# Terminal 1: Start server with auto-reload
npm run dev

# Terminal 2: Start tunnel
npm run tunnel

# Terminal 3: Fire test triggers
npm run test:trigger
```

### Step 6: Environment Configuration

```bash
# .env
LINDY_WEBHOOK_URL=https://public.lindy.ai/api/v1/webhooks/YOUR_ID
LINDY_TRIGGER_SECRET=replace-with-development-trigger-secret
LINDY_CALLBACK_SECRET=replace-with-different-callback-secret
NODE_ENV=development
```

## Development Workflow

```
[Edit local code] → [Auto-reload via tsx watch]
                          ↓
[Fire test webhook] → [Lindy agent processes]
                          ↓
[Agent calls back] → [ngrok tunnel → localhost:3000]
                          ↓
[Review logs] → [Iterate]
```

## Output

Produce a local-test receipt containing the callback route, redacted tunnel
origin, test payload fixture, authenticated and unauthenticated HTTP outcomes,
Lindy task ID, callback status, and log timestamp. The receipt must not contain
the tunnel's private path, either bearer credential, or any customer payload.

## Examples

Start the receiver and tunnel, send a synthetic event with the development
credential, and confirm one callback is accepted and correlated to the recorded
task ID. Send the same fixture without authorization and confirm a 401 response.
If the tunnel changes, update only the development configuration and rerun both
checks before continuing iteration.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ngrok tunnel expires | Free tier limit (2hr) | Restart ngrok or use paid plan |
| Lindy can't reach endpoint | Tunnel URL changed | Update webhook URL in Lindy dashboard |
| Callback not received | Agent HTTP Request misconfigured | Check URL and headers in action config |
| `ECONNREFUSED` | Local server not running | Start server before testing |
| SSL error | ngrok not using HTTPS | Always use the `https://` ngrok URL |

## Resources

- [Webhook Triggers](https://www.lindy.ai/academy-lessons/webhook-triggers)
- [Calling Any API](https://www.lindy.ai/academy-lessons/calling-any-api)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps

Proceed to `lindy-sdk-patterns` for integration patterns and best practices.
