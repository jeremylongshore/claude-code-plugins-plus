---
name: lindy-local-dev-loop
description: |
  Set up local development workflow for testing Lindy AI agent integrations.
  Use when building webhook receivers, testing agent callbacks,
  or iterating on Lindy-connected applications locally.
  Trigger with phrases like "lindy local dev", "lindy development",
  "test lindy locally", "lindy webhook local".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, testing, workflow]

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

const WEBHOOK_SECRET = process.env.LINDY_WEBHOOK_SECRET;

// Verify Lindy webhook authenticity
function verifyWebhook(req: express.Request): boolean {
  const auth = req.headers.authorization;
  return auth === `Bearer ${WEBHOOK_SECRET}`;
}

// Receive Lindy agent callbacks
app.post('/lindy/callback', (req, res) => {
  if (!verifyWebhook(req)) {
    console.error('Unauthorized webhook attempt');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  console.log('Lindy callback received:', JSON.stringify(req.body, null, 2));

  // Process the agent's output
  const { taskId, result, status } = req.body;
  console.log(`Task ${taskId}: ${status}`);

  res.json({ received: true });
});

// Health check for Lindy to verify endpoint
app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.listen(3000, () => console.log('Webhook receiver running on :3000'));
```

### Step 2: Expose Local Server via Tunnel
```bash
# Install and start ngrok
npm install -g ngrok
ngrok http 3000

# Output: https://abc123.ngrok.io -> http://localhost:3000
# Use this URL in Lindy webhook configuration
```

### Step 3: Configure Lindy Agent to Call Your Endpoint
In the Lindy dashboard, add an **HTTP Request** action to your agent:
- **Method**: POST
- **URL**: `https://abc123.ngrok.io/lindy/callback`
- **Headers**: `Content-Type: application/json`
- **Body** (AI Prompt mode):
  ```
  Send the task result as JSON with fields: taskId, result, status
  ```

Or configure a webhook trigger pointing to your tunnel URL:
```
https://abc123.ngrok.io/lindy/webhook
```

### Step 4: Create Test Harness
```typescript
// test-trigger.ts — Fire a test webhook to your Lindy agent
import fetch from 'node-fetch';

async function triggerAgent() {
  const WEBHOOK_URL = process.env.LINDY_WEBHOOK_URL!;
  const SECRET = process.env.LINDY_WEBHOOK_SECRET!;

  const response = await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SECRET}`,
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
LINDY_API_KEY=lnd_live_xxxxxxxxxxxx
LINDY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
LINDY_WEBHOOK_URL=https://public.lindy.ai/api/v1/webhooks/YOUR_ID
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
