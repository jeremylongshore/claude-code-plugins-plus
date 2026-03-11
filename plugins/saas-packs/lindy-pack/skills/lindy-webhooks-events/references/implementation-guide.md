# Lindy Webhooks Events - Implementation Guide

# Lindy Webhooks & Events

## Overview
Configure webhooks and event-driven integrations with Lindy AI.

## Prerequisites
- Lindy account with webhook access
- HTTPS endpoint for receiving webhooks
- Understanding of event types

## Instructions

### Step 1: Register Webhook
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

async function registerWebhook() {
  const webhook = await lindy.webhooks.create({
    url: 'https://myapp.com/webhooks/lindy',
    events: [
      'agent.run.started',
      'agent.run.completed',
      'agent.run.failed',
      'automation.triggered',
    ],
    secret: process.env.WEBHOOK_SECRET,
  });

  console.log(`Webhook ID: ${webhook.id}`);
  return webhook;
}
```

### Step 2: Create Webhook Handler
```typescript
// routes/webhooks/lindy.ts
import express from 'express';
import crypto from 'crypto';

const router = express.Router();

function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${expected}`)
  );
}

router.post('/lindy', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-lindy-signature'] as string;
  const payload = req.body.toString();

  // Verify signature
  if (!verifySignature(payload, signature, process.env.WEBHOOK_SECRET!)) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(payload);

  // Handle event
  switch (event.type) {
    case 'agent.run.completed':
      handleRunCompleted(event.data);
      break;
    case 'agent.run.failed':
      handleRunFailed(event.data);
      break;
    case 'automation.triggered':
      handleAutomationTriggered(event.data);
      break;
    default:
      console.log('Unhandled event:', event.type);
  }

  res.status(200).send('OK');
});

export default router;
```

### Step 3: Implement Event Handlers
```typescript
// handlers/lindy-events.ts

interface RunCompletedEvent {
  runId: string;
  agentId: string;
  input: string;
  output: string;
  duration: number;
}

interface RunFailedEvent {
  runId: string;
  agentId: string;
  error: string;
  errorCode: string;
}

async function handleRunCompleted(data: RunCompletedEvent) {
  console.log(`Run ${data.runId} completed in ${data.duration}ms`);

  // Store result
  await db.runs.create({
    runId: data.runId,
    agentId: data.agentId,
    output: data.output,
    status: 'completed',
  });

  // Trigger downstream actions
  await processResult(data);
}

async function handleRunFailed(data: RunFailedEvent) {
  console.error(`Run ${data.runId} failed: ${data.error}`);

  // Alert on failure
  await alerting.send({
    severity: 'high',
    message: `Lindy agent failed: ${data.errorCode}`,
    details: data,
  });

  // Retry if appropriate
  if (data.errorCode === 'TIMEOUT') {
    await retryRun(data.runId);
  }
}

async function handleAutomationTriggered(data: any) {
  console.log(`Automation ${data.automationId} triggered`);

  // Log automation trigger
  await db.automations.log({
    automationId: data.automationId,
    triggeredAt: new Date(),
    input: data.input,
  });
}
```

### Step 4: Test Webhooks
```typescript
// Test webhook delivery
async function testWebhook(webhookId: string) {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  const result = await lindy.webhooks.test(webhookId, {
    type: 'agent.run.completed',
    data: {
      runId: 'test_run_123',
      agentId: 'agt_test',
      output: 'Test output',
      duration: 1000,
    },
  });

  console.log('Test result:', result);
}
```

## Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.run.started` | Agent run began | runId, agentId, input |
| `agent.run.completed` | Agent run finished | runId, output, duration |
| `agent.run.failed` | Agent run failed | runId, error, errorCode |
| `automation.triggered` | Automation fired | automationId, input |
| `agent.created` | New agent created | agentId, name |
| `agent.deleted` | Agent deleted | agentId |

## Output
- Registered webhooks
- Event handler implementation
- Signature verification
- Event logging

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Check WEBHOOK_SECRET |
| Timeout | Handler slow | Respond quickly, process async |
| Duplicate events | Retry delivery | Implement idempotency |

## Examples

### Async Processing Pattern
```typescript
router.post('/lindy', async (req, res) => {
  // Verify signature first
  if (!verifySignature(req)) {
    return res.status(401).send('Invalid');
  }

  // Acknowledge immediately
  res.status(200).send('OK');

  // Process asynchronously
  const event = JSON.parse(req.body);
  await queue.push('lindy-events', event);
});
```

## Resources
- [Lindy Webhooks](https://docs.lindy.ai/webhooks)
- [Event Reference](https://docs.lindy.ai/webhooks/events)
- [Security Best Practices](https://docs.lindy.ai/webhooks/security)

## Next Steps
Proceed to `lindy-performance-tuning` for optimization.
