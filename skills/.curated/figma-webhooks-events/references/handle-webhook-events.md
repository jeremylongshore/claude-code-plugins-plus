# Step 2: Handle Webhook Events

Deep-dive reference for the `figma-webhooks-events` skill — extracted from the 'Step 2: Handle Webhook Events' step of the workflow.

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json());

// Figma webhook payload types
interface FigmaWebhookBase {
  event_type: string;
  passcode: string;
  timestamp: string;
  webhook_id: string;
}

interface FileUpdateEvent extends FigmaWebhookBase {
  event_type: 'FILE_UPDATE';
  file_key: string;
  file_name: string;
  triggered_by: { id: string; handle: string };
}

interface FileCommentEvent extends FigmaWebhookBase {
  event_type: 'FILE_COMMENT';
  file_key: string;
  file_name: string;
  comment: Array<{ text: string }>;
  comment_id: string;
  triggered_by: { id: string; handle: string };
}

interface LibraryPublishEvent extends FigmaWebhookBase {
  event_type: 'LIBRARY_PUBLISH';
  file_key: string;
  file_name: string;
  description: string;
  triggered_by: { id: string; handle: string };
}

type FigmaWebhookEvent = FileUpdateEvent | FileCommentEvent | LibraryPublishEvent;

app.post('/webhooks/figma', (req, res) => {
  const event: FigmaWebhookEvent = req.body;

  // 1. Verify passcode (timing-safe)
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;
  if (event.passcode.length !== expected.length ||
      !crypto.timingSafeEqual(Buffer.from(event.passcode), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  // 2. Respond quickly (Figma expects 200 within seconds)
  res.status(200).json({ received: true });

  // 3. Process async
  processEvent(event).catch(err =>
    console.error(`Failed to process ${event.event_type}:`, err)
  );
});

async function processEvent(event: FigmaWebhookEvent) {
  switch (event.event_type) {
    case 'FILE_UPDATE':
      console.log(`File updated: ${event.file_name} by ${event.triggered_by.handle}`);
      // Re-extract design tokens, invalidate cache, notify Slack
      await syncDesignTokens(event.file_key);
      break;

    case 'FILE_COMMENT':
      console.log(`Comment on ${event.file_name}: ${event.comment[0]?.text}`);
      // Forward to Slack, create Jira ticket, etc.
      break;

    case 'LIBRARY_PUBLISH':
      console.log(`Library published: ${event.file_name}`);
      // Trigger downstream rebuilds
      await triggerTokenRebuild(event.file_key);
      break;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
