# Documenso Webhooks & Events - Implementation Guide

## Supported Events

| Event | Trigger | Description |
|-------|---------|-------------|
| `document.created` | Document created | New document added to system |
| `document.sent` | Document sent | Document sent to recipients |
| `document.opened` | Document opened | Recipient opened document |
| `document.signed` | Recipient signed | One recipient completed signing |
| `document.completed` | All signed | All recipients have signed |
| `document.rejected` | Document rejected | Recipient rejected document |
| `document.cancelled` | Document cancelled | Document was cancelled |

## Webhook Setup

### Step 1: Create Webhook in Dashboard

1. Log into Documenso dashboard
2. Click avatar -> "Team settings"
3. Navigate to "Webhooks" tab
4. Click "Create Webhook"
5. Configure:
   - **URL**: Your HTTPS endpoint
   - **Events**: Select events to subscribe
   - **Secret**: Optional but recommended

### Step 2: Implement Webhook Endpoint

```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// IMPORTANT: Use raw body parser for signature verification
app.use("/webhooks/documenso", express.raw({ type: "application/json" }));

interface DocumensoWebhookPayload {
  event:
    | "document.created"
    | "document.sent"
    | "document.opened"
    | "document.signed"
    | "document.completed"
    | "document.rejected"
    | "document.cancelled";
  payload: {
    id: string;
    title: string;
    status: string;
    createdAt: string;
    updatedAt: string;
    documentDataId: string;
    userId: string;
    teamId?: string;
    recipients: Array<{
      id: string;
      email: string;
      name: string;
      role: string;
      signingStatus: string;
      signedAt?: string;
    }>;
  };
  createdAt: string;
  webhookEndpoint: string;
}

app.post("/webhooks/documenso", async (req, res) => {
  // Step 1: Verify webhook secret
  const receivedSecret = req.headers["x-documenso-secret"] as string;
  const expectedSecret = process.env.DOCUMENSO_WEBHOOK_SECRET;

  if (expectedSecret && receivedSecret !== expectedSecret) {
    console.warn("Invalid webhook secret");
    return res.status(401).json({ error: "Invalid signature" });
  }

  // Step 2: Parse payload
  let payload: DocumensoWebhookPayload;
  try {
    payload = JSON.parse(req.body.toString());
  } catch (error) {
    console.error("Invalid JSON payload");
    return res.status(400).json({ error: "Invalid JSON" });
  }

  // Step 3: Log event
  console.log(`Webhook received: ${payload.event}`);
  console.log(`Document: ${payload.payload.id} - ${payload.payload.title}`);

  // Step 4: Handle event
  try {
    await handleWebhookEvent(payload);
    res.status(200).json({ received: true });
  } catch (error) {
    console.error("Webhook handling error:", error);
    res.status(500).json({ error: "Internal error" });
  }
});

async function handleWebhookEvent(
  webhook: DocumensoWebhookPayload
): Promise<void> {
  const { event, payload } = webhook;

  switch (event) {
    case "document.created":
      await onDocumentCreated(payload);
      break;
    case "document.sent":
      await onDocumentSent(payload);
      break;
    case "document.opened":
      await onDocumentOpened(payload);
      break;
    case "document.signed":
      await onDocumentSigned(payload);
      break;
    case "document.completed":
      await onDocumentCompleted(payload);
      break;
    case "document.rejected":
      await onDocumentRejected(payload);
      break;
    case "document.cancelled":
      await onDocumentCancelled(payload);
      break;
    default:
      console.log(`Unhandled event: ${event}`);
  }
}
```

### Step 3: Event Handlers

```typescript
async function onDocumentCreated(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  console.log(`Document created: ${doc.title}`);

  // Track in your system
  await db.documents.create({
    externalId: doc.id,
    title: doc.title,
    status: "created",
    createdAt: new Date(doc.createdAt),
  });
}

async function onDocumentSent(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  console.log(`Document sent: ${doc.title}`);

  // Update status
  await db.documents.update({
    where: { externalId: doc.id },
    data: { status: "sent", sentAt: new Date() },
  });

  // Notify internal users
  await notifications.send({
    channel: "slack",
    message: `Document "${doc.title}" sent to ${doc.recipients.length} recipients`,
  });
}

async function onDocumentOpened(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  // Find who opened it
  const opener = doc.recipients.find(
    (r) => r.signingStatus === "NOT_SIGNED" // They opened but haven't signed
  );

  console.log(`Document opened by: ${opener?.email}`);

  // Track for analytics
  await analytics.track("document_opened", {
    documentId: doc.id,
    recipientEmail: opener?.email,
  });
}

async function onDocumentSigned(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  // Find who signed
  const signer = doc.recipients.find((r) => r.signingStatus === "SIGNED");

  console.log(`Document signed by: ${signer?.email}`);

  // Update tracking
  await db.signatures.create({
    documentId: doc.id,
    recipientEmail: signer?.email,
    signedAt: signer?.signedAt ? new Date(signer.signedAt) : new Date(),
  });

  // Check if all have signed
  const allSigned = doc.recipients.every(
    (r) => r.role === "CC" || r.signingStatus === "SIGNED"
  );

  if (allSigned) {
    console.log("All recipients have signed!");
  }
}

async function onDocumentCompleted(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  console.log(`Document completed: ${doc.title}`);

  // Update status
  await db.documents.update({
    where: { externalId: doc.id },
    data: { status: "completed", completedAt: new Date() },
  });

  // Download signed document
  const client = getDocumensoClient();
  const signedDoc = await client.documents.downloadV0({
    documentId: doc.id,
  });

  // Store signed copy
  await storage.upload(`signed/${doc.id}.pdf`, signedDoc);

  // Trigger downstream processes
  await workflows.trigger("document_completed", {
    documentId: doc.id,
    title: doc.title,
  });
}

async function onDocumentRejected(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  const rejecter = doc.recipients.find((r) => r.signingStatus === "REJECTED");

  console.log(`Document rejected by: ${rejecter?.email}`);

  // Update status
  await db.documents.update({
    where: { externalId: doc.id },
    data: { status: "rejected", rejectedBy: rejecter?.email },
  });

  // Alert team
  await notifications.send({
    channel: "slack",
    priority: "high",
    message: `Document "${doc.title}" rejected by ${rejecter?.email}`,
  });
}

async function onDocumentCancelled(
  doc: DocumensoWebhookPayload["payload"]
): Promise<void> {
  console.log(`Document cancelled: ${doc.title}`);

  // Update status
  await db.documents.update({
    where: { externalId: doc.id },
    data: { status: "cancelled", cancelledAt: new Date() },
  });
}
```

### Step 4: Idempotency

```typescript
// Prevent duplicate processing
const processedWebhooks = new Set<string>();

async function handleWebhookIdempotent(
  webhook: DocumensoWebhookPayload
): Promise<boolean> {
  // Create unique key from event + document + timestamp
  const key = `${webhook.event}:${webhook.payload.id}:${webhook.createdAt}`;

  // Check if already processed
  if (processedWebhooks.has(key)) {
    console.log(`Duplicate webhook ignored: ${key}`);
    return false;
  }

  // Mark as processed
  processedWebhooks.add(key);

  // Cleanup old entries (keep last 10000)
  if (processedWebhooks.size > 10000) {
    const oldest = processedWebhooks.values().next().value;
    processedWebhooks.delete(oldest);
  }

  // Process webhook
  await handleWebhookEvent(webhook);
  return true;
}

// For production, use Redis or database
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

async function handleWebhookIdempotentRedis(
  webhook: DocumensoWebhookPayload
): Promise<boolean> {
  const key = `webhook:${webhook.event}:${webhook.payload.id}:${webhook.createdAt}`;

  // Try to set key with 7 day expiry
  const result = await redis.set(key, "1", "EX", 604800, "NX");

  if (!result) {
    console.log(`Duplicate webhook: ${key}`);
    return false;
  }

  await handleWebhookEvent(webhook);
  return true;
}
```

## Local Development

```bash
# Start ngrok tunnel
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Configure this URL in Documenso webhook settings
# Your endpoint: https://abc123.ngrok.io/webhooks/documenso
```

## Testing Webhooks

```bash
# Test webhook endpoint locally
curl -X POST http://localhost:3000/webhooks/documenso \
  -H "Content-Type: application/json" \
  -H "X-Documenso-Secret: your-secret" \
  -d '{
    "event": "document.completed",
    "payload": {
      "id": "doc_test123",
      "title": "Test Document",
      "status": "COMPLETED",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T01:00:00Z",
      "recipients": [
        {
          "id": "rec_123",
          "email": "signer@example.com",
          "name": "Test Signer",
          "role": "SIGNER",
          "signingStatus": "SIGNED"
        }
      ]
    },
    "createdAt": "2024-01-01T01:00:00Z",
    "webhookEndpoint": "https://yourapp.com/webhooks/documenso"
  }'
```
