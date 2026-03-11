# Lokalise Webhooks Events - Implementation Guide

Detailed implementation reference for the lokalise-webhooks-events skill.

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `project.imported` | File uploaded | File details, key counts |
| `project.exported` | File downloaded | Export details |
| `project.key.added` | New key created | Key data |
| `project.keys.added` | Bulk keys added | Array of keys (max 300) |
| `project.key.modified` | Key updated | Key data with changes |
| `project.key.deleted` | Key removed | Key ID |
| `project.translation.updated` | Translation changed | Translation data |
| `project.translations.updated` | Bulk updates | Array of translations |
| `project.task.closed` | Task completed | Task details |
| `project.branch.merged` | Branch merged | Branch info |
| `project.contributor.added` | User added | Contributor data |


## Instructions

### Step 1: Set Up Webhook Endpoint
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

// IMPORTANT: Use raw body for signature verification
app.post("/webhooks/lokalise",
  express.raw({ type: "application/json" }),
  async (req, res) => {
    // Verify signature
    const receivedSecret = req.headers["x-secret"] as string;
    const expectedSecret = process.env.LOKALISE_WEBHOOK_SECRET!;

    if (!verifySecret(receivedSecret, expectedSecret)) {
      console.error("Invalid webhook secret");
      return res.status(401).json({ error: "Invalid signature" });
    }

    // Parse and handle event
    const event = JSON.parse(req.body.toString());
    console.log(`Received event: ${event.event}`);

    // Respond quickly, process async
    res.status(200).json({ received: true });

    // Process event asynchronously
    await handleLokaliseEvent(event);
  }
);

function verifySecret(received: string, expected: string): boolean {
  if (!received || !expected) return false;
  return crypto.timingSafeEqual(
    Buffer.from(received),
    Buffer.from(expected)
  );
}
```

### Step 2: Event Handler Router
```typescript
type LokaliseEventType =
  | "project.imported"
  | "project.exported"
  | "project.key.added"
  | "project.keys.added"
  | "project.key.modified"
  | "project.key.deleted"
  | "project.translation.updated"
  | "project.translations.updated"
  | "project.task.closed"
  | "project.branch.merged";

interface LokaliseWebhookPayload {
  event: LokaliseEventType;
  project: {
    id: string;
    name: string;
  };
  user?: {
    email: string;
    full_name: string;
  };
  action?: string;
  // Event-specific data
  [key: string]: any;
}

const eventHandlers: Record<LokaliseEventType, (payload: any) => Promise<void>> = {
  "project.imported": handleFileImported,
  "project.exported": handleFileExported,
  "project.key.added": handleKeyAdded,
  "project.keys.added": handleKeysAdded,
  "project.key.modified": handleKeyModified,
  "project.key.deleted": handleKeyDeleted,
  "project.translation.updated": handleTranslationUpdated,
  "project.translations.updated": handleTranslationsUpdated,
  "project.task.closed": handleTaskClosed,
  "project.branch.merged": handleBranchMerged,
};

async function handleLokaliseEvent(payload: LokaliseWebhookPayload): Promise<void> {
  const handler = eventHandlers[payload.event];

  if (!handler) {
    console.log(`Unhandled event type: ${payload.event}`);
    return;
  }

  try {
    await handler(payload);
    console.log(`Processed ${payload.event} successfully`);
  } catch (error) {
    console.error(`Failed to process ${payload.event}:`, error);
    // Implement retry logic or dead letter queue
    throw error;
  }
}
```

### Step 3: Implement Event Handlers
```typescript
async function handleFileImported(payload: any): Promise<void> {
  const { project, file, import_details } = payload;

  console.log(`File imported to ${project.name}: ${file.filename}`);
  console.log(`Keys added: ${import_details.keys_added}`);
  console.log(`Keys updated: ${import_details.keys_updated}`);

  // Trigger CI/CD pipeline to rebuild with new translations
  if (import_details.keys_added > 0 || import_details.keys_updated > 0) {
    await triggerBuildPipeline(project.id);
  }
}

async function handleTranslationUpdated(payload: any): Promise<void> {
  const { project, translation, language } = payload;

  console.log(`Translation updated in ${project.name}`);
  console.log(`Key: ${translation.key_name}, Language: ${language.lang_iso}`);

  // Invalidate cache for this translation
  await invalidateTranslationCache(
    project.id,
    translation.key_name,
    language.lang_iso
  );
}

async function handleTaskClosed(payload: any): Promise<void> {
  const { project, task } = payload;

  console.log(`Task "${task.title}" completed in ${project.name}`);

  // Notify team via Slack
  await sendSlackNotification({
    channel: "#translations",
    text: `Translation task completed: ${task.title}\nLanguages: ${task.languages.join(", ")}`,
  });

  // Trigger download of completed translations
  await downloadTranslations(project.id, task.languages);
}

async function handleBranchMerged(payload: any): Promise<void> {
  const { project, branch } = payload;

  console.log(`Branch "${branch.name}" merged to main`);

  // Sync translations after branch merge
  await syncTranslationsAfterMerge(project.id);
}

async function handleKeysAdded(payload: any): Promise<void> {
  const { project, keys } = payload;

  console.log(`${keys.length} keys added to ${project.name}`);

  // Note: Payload limited to 300 keys per event
  // If more keys were added, you'll receive multiple events

  for (const key of keys) {
    await indexKeyForSearch(project.id, key);
  }
}
```

### Step 4: Configure Webhook in Lokalise
```typescript
import { LokaliseApi } from "@lokalise/node-api";

const client = new LokaliseApi({
  apiKey: process.env.LOKALISE_API_TOKEN!,
});

async function setupWebhook(projectId: string) {
  const webhook = await client.webhooks().create({
    project_id: projectId,
    url: "https://api.yourapp.com/webhooks/lokalise",
    events: [
      "project.imported",
      "project.translation.updated",
      "project.task.closed",
      "project.branch.merged",
    ],
    event_lang_map: [
      { event: "project.translation.updated", lang_iso_codes: ["es", "fr", "de"] },
    ],
  });

  console.log(`Webhook created with ID: ${webhook.webhook_id}`);
  console.log(`Secret: ${webhook.secret}`);  // Store this securely!

  return webhook;
}
```


## Detailed Examples

### Idempotent Event Processing
```typescript
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

async function processEventIdempotently(
  eventId: string,
  handler: () => Promise<void>
): Promise<boolean> {
  const key = `lokalise:event:${eventId}`;

  // Try to set key (returns null if already exists)
  const acquired = await redis.set(key, "1", "EX", 86400, "NX");

  if (!acquired) {
    console.log(`Event ${eventId} already processed, skipping`);
    return false;
  }

  await handler();
  return true;
}

// Usage
app.post("/webhooks/lokalise", async (req, res) => {
  const event = JSON.parse(req.body);
  const eventId = `${event.event}-${event.created}-${event.project.id}`;

  res.status(200).json({ received: true });

  await processEventIdempotently(eventId, () =>
    handleLokaliseEvent(event)
  );
});
```

### Testing Webhooks Locally
```bash
# Use ngrok to expose local server
ngrok http 3000

# Test with curl
curl -X POST https://your-ngrok-url/webhooks/lokalise \
  -H "Content-Type: application/json" \
  -H "X-Secret: your-webhook-secret" \
  -d '{
    "event": "project.translation.updated",
    "project": {"id": "123", "name": "Test"},
    "translation": {"key_name": "test.key"}
  }'
```

### Auto-Rebuild on Translation Update
```typescript
async function handleTranslationsUpdated(payload: any): Promise<void> {
  const { project, translations, action } = payload;

  // Only trigger rebuild if action is from import or API
  if (action === "import.file" || action === "api.update") {
    console.log(`Triggering rebuild for ${translations.length} updated translations`);

    // Trigger Vercel deployment hook
    await fetch(process.env.VERCEL_DEPLOY_HOOK!, {
      method: "POST",
    });
  }
}
```

