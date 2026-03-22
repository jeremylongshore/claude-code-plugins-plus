---
name: lindy-webhooks-events
description: |
  Configure Lindy AI webhook triggers, callback patterns, and event handling.
  Use when setting up webhook triggers, implementing callback receivers,
  or building event-driven Lindy integrations.
  Trigger with phrases like "lindy webhook", "lindy events",
  "lindy callback", "lindy webhook trigger".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, webhooks]

---
# Lindy Webhooks & Events

## Overview
Lindy supports webhooks in two directions: **Inbound** (Webhook Received trigger
wakes an agent) and **Outbound** (HTTP Request action calls your API). This skill
covers both patterns, plus the callback pattern for async two-way communication.

## Prerequisites
- Lindy account with active agents
- HTTPS endpoint for receiving callbacks (if using outbound/callback patterns)
- Completed `lindy-install-auth` setup

## Webhook Architecture

```
INBOUND (your system triggers Lindy):
[Your App] --POST--> https://public.lindy.ai/api/v1/webhooks/<id>
                         ↓
                    [Lindy Agent Wakes Up]
                         ↓
                    [Processes with LLM]
                         ↓
                    [Executes Actions]

OUTBOUND (Lindy calls your system):
[Lindy Agent] --HTTP Request action--> https://your-api.com/endpoint
                                            ↓
                                       [Your Handler]

CALLBACK (two-way async):
[Your App] --POST with callbackUrl--> [Lindy Agent]
                                          ↓
[Your App] <--POST to callbackUrl-- [Lindy: Send POST to Callback]
```

## Instructions

### Step 1: Create Webhook Received Trigger
1. In your agent, click the trigger node
2. Select **Webhook Received**
3. Lindy generates a unique URL:
   ```
   https://public.lindy.ai/api/v1/webhooks/<unique-id>
   ```
4. Click **Generate Secret** — copy immediately (shown only once)
5. Configure follow-up processing mode:
   - **Process in workflow**: Handle in current workflow
   - **Spawn separate task**: Each webhook creates a new task
   - **Discard follow-ups**: Ignore subsequent requests while processing

### Step 2: Access Webhook Data in Workflow
Reference incoming webhook data in any subsequent action field:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{webhook_received.request.body}}` | Full JSON payload | `{"event": "order.created", ...}` |
| `{{webhook_received.request.body.event}}` | Specific field | `"order.created"` |
| `{{webhook_received.request.headers}}` | All HTTP headers | `{"content-type": "application/json"}` |
| `{{webhook_received.request.query}}` | URL query params | `{"source": "stripe"}` |

### Step 3: Implement Webhook Sender
```typescript
// webhook-sender.ts — Trigger Lindy agents from your application
interface LindyWebhookPayload {
  event: string;
  data: Record<string, unknown>;
  callbackUrl?: string;
  metadata?: Record<string, unknown>;
}

async function triggerLindy(payload: LindyWebhookPayload): Promise<void> {
  const response = await fetch(process.env.LINDY_WEBHOOK_URL!, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Lindy webhook failed: ${response.status}`);
  }
}

// Usage examples:
await triggerLindy({
  event: 'customer.support_request',
  data: { email: 'user@co.com', subject: 'Billing question', body: '...' },
});

await triggerLindy({
  event: 'lead.qualified',
  data: { name: 'Jane Doe', company: 'Acme', score: 85 },
  callbackUrl: 'https://api.yourapp.com/lindy/callback',
});
```

### Step 4: Implement Callback Receiver
When you include a `callbackUrl` in your webhook payload, the agent can respond
using the **Send POST Request to Callback** action:

```typescript
// callback-receiver.ts
import express from 'express';

const app = express();
app.use(express.json());

// Receive Lindy agent results
app.post('/lindy/callback', (req, res) => {
  // Verify authenticity
  const auth = req.headers.authorization;
  if (auth !== `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Respond immediately (Lindy expects a quick response)
  res.json({ received: true });

  // Process async
  handleCallback(req.body);
});

async function handleCallback(data: any) {
  console.log('Lindy callback:', data);

  // Example: Agent analyzed a support ticket
  const { classification, sentiment, draft_response, confidence } = data;

  if (confidence > 0.9) {
    await sendAutoResponse(draft_response);
  } else {
    await escalateToHuman(data);
  }
}
```

### Step 5: Configure HTTP Request Action (Outbound)
For Lindy agents that call your API as an action step:

1. Add action: **HTTP Request**
2. Configure:
   - **Method**: POST (or GET, PUT, DELETE)
   - **URL**: `https://api.yourapp.com/endpoint`
   - **Headers** (Set Manually):
     ```
     Content-Type: application/json
     Authorization: Bearer {{your_api_key}}
     ```
   - **Body** (AI Prompt mode):
     ```
     Send the analysis result as JSON with fields:
     classification, sentiment, summary
     Based on: {{previous_step.result}}
     ```

### Step 6: Add Trigger Filters
Prevent unnecessary agent triggers:
```
Filter: body.event equals "order.created"
  AND body.data.amount greater_than 100
```

This ensures the agent only processes high-value orders, saving credits.

## Event Patterns

### Pattern: Webhook + Slack Notification
```
Webhook Received → Condition (classify event type)
  → "billing" → Search KB → Draft Reply → Send Email + Slack Alert
  → "technical" → Agent Step (investigate) → Create Ticket → Slack Alert
  → "other" → Forward to team inbox
```

### Pattern: Webhook + Callback
```
Webhook Received (with callbackUrl) → Process Data → Run Code
  → Send POST Request to Callback (returns results to caller)
```

### Pattern: Webhook + Multi-Agent
```
Webhook Received → Agent Send Message (to Research Lindy)
  → Research Lindy completes → Agent Send Message (to Writer Lindy)
  → Writer Lindy completes → Send Email with final output
```

## Monitoring Triggers
Lindy provides built-in monitoring triggers:
- **Task Completed**: Fires when an agent completes a task
- Use this to build observability pipelines: Agent completes → log to sheet → alert on failures

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 on webhook send | Wrong or missing Bearer token | Verify secret matches Generate Secret value |
| Webhook URL returns 404 | Agent deleted or URL changed | Re-copy URL from agent trigger settings |
| Callback not received | callbackUrl unreachable | Ensure HTTPS, public endpoint, no firewall |
| Duplicate processing | Webhook retried | Implement idempotency with event IDs |
| Payload too large | Body exceeds limit | Reduce payload size, send references not data |

## Security
- Always use HTTPS for webhook URLs
- Generate and verify webhook secrets on every request
- Rotate secrets every 90 days
- Log all webhook attempts (including rejected ones)
- Rate limit your webhook sender to prevent flooding

## Resources
- [Webhooks Documentation](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Webhook Triggers Academy](https://www.lindy.ai/academy-lessons/webhook-triggers)
- [Calling Any API](https://www.lindy.ai/academy-lessons/calling-any-api)

## Next Steps
Proceed to `lindy-performance-tuning` for agent optimization.
