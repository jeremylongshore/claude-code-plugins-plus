# Webhook Handler Examples

## Signature Verification and Endpoint Setup

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

## Event Router

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

## Call Result Processing

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

## Outbound Call via API

```bash
set -euo pipefail
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

## Post-Call Action Items

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
