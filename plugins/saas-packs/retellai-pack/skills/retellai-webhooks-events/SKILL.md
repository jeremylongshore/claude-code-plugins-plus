---
name: retellai-webhooks-events
description: |
  Implement Retell AI webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Retell AI event notifications securely.
  Trigger with phrases like "retellai webhook", "retellai events",
  "retellai webhook signature", "handle retellai events", "retellai notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Retell AI Webhooks & Events

## Overview
Handle Retell AI webhooks for real-time voice call lifecycle events. Retell AI fires webhooks when calls start, end, or encounter events during conversation. Use these to build real-time call monitoring dashboards, post-call processing pipelines, and automated follow-up workflows for AI voice agents.

## Prerequisites
- Retell AI account with API access
- Retell AI API key stored in `RETELL_API_KEY` environment variable
- HTTPS endpoint for receiving webhook deliveries
- Voice agent configured in Retell AI dashboard

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `call_started` | AI agent picks up | Call ID, agent ID, from/to numbers |
| `call_ended` | Call completes | Call ID, duration, end reason, transcript |
| `call_analyzed` | Post-call analysis done | Sentiment, summary, custom data |
| `agent_transfer` | Transfer to human | Call ID, transfer number, context |
| `voicemail_detected` | Voicemail reached | Call ID, voicemail status |
| `call_error` | Call fails | Error code, error message |

## Instructions

### Step 1: Configure Webhook Endpoint
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

app.post("/webhooks/retellai",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    const signature = req.headers["x-retell-signature"] as string;
    const secret = process.env.RETELL_WEBHOOK_SECRET!;

    const expected = crypto
      .createHmac("sha256", secret)
      .update(req.body)
      .digest("hex");

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());
    res.status(200).json({ received: true });
    await handleRetellEvent(event);
  }
);
```

### Step 2: Route Call Events
```typescript
interface RetellWebhookPayload {
  event: string;
  call: {
    call_id: string;
    agent_id: string;
    call_status: string;
    from_number: string;
    to_number: string;
    duration_ms?: number;
    transcript?: string;
    call_analysis?: {
      sentiment: string;
      summary: string;
      custom_analysis_data: Record<string, any>;
    };
  };
}

async function handleRetellEvent(payload: RetellWebhookPayload) {
  switch (payload.event) {
    case "call_started":
      await handleCallStarted(payload.call);
      break;
    case "call_ended":
      await handleCallEnded(payload.call);
      break;
    case "call_analyzed":
      await handleCallAnalyzed(payload.call);
      break;
    case "agent_transfer":
      await handleAgentTransfer(payload.call);
      break;
  }
}
```

### Step 3: Process Call Results
```typescript
async function handleCallEnded(call: any) {
  const { call_id, duration_ms, transcript, from_number } = call;
  const durationMin = Math.round(duration_ms / 60000);

  console.log(`Call ${call_id} ended: ${durationMin}min`);

  await db.calls.create({
    callId: call_id,
    fromNumber: from_number,
    duration: duration_ms,
    transcript,
    completedAt: new Date(),
  });

  if (transcript) {
    await extractActionItems(call_id, transcript);
  }
}

async function handleCallAnalyzed(call: any) {
  const { call_id, call_analysis } = call;
  const { sentiment, summary } = call_analysis;

  if (sentiment === "negative") {
    await alerting.send({
      channel: "#customer-escalations",
      message: `Negative call: ${call_id}\nSummary: ${summary}`,
    });
  }

  await crmClient.logActivity({
    callId: call_id,
    sentiment,
    summary,
  });
}
```

### Step 4: Create Outbound Call via API
```bash
curl -X POST https://api.retellai.com/v2/create-phone-call \
  -H "Authorization: Bearer $RETELL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_number": "+11234567890",
    "to_number": "+10987654321",
    "agent_id": "agt_abc123",
    "webhook_url": "https://api.yourapp.com/webhooks/retellai"
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify secret in Retell AI dashboard |
| No transcript | Short call or error | Check `end_reason` for early termination |
| Transfer failed | Invalid transfer number | Verify transfer number is active |
| Missing analysis | Analysis not configured | Enable post-call analysis in agent settings |

## Examples

### Post-Call Action Items
```typescript
async function extractActionItems(callId: string, transcript: string) {
  const items = await llm.extract(transcript, "action_items");
  for (const item of items) {
    await taskManager.createTask({
      title: item,
      source: `Call: ${callId}`,
    });
  }
}
```

## Resources
- [Retell AI API Documentation](https://docs.retellai.com)
- [Retell AI Webhooks](https://docs.retellai.com/webhooks)

## Next Steps
For deployment setup, see `retellai-deploy-integration`.
