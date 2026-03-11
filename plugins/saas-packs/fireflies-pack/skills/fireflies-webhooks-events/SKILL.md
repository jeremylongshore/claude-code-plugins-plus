---
name: fireflies-webhooks-events
description: |
  Implement Fireflies.ai webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Fireflies.ai event notifications securely.
  Trigger with phrases like "fireflies webhook", "fireflies events",
  "fireflies webhook signature", "handle fireflies events", "fireflies notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Fireflies.ai Webhooks & Events

## Overview
Handle Fireflies.ai webhooks for real-time meeting transcript notifications. Fireflies sends webhook events when meeting transcripts are ready, when action items are extracted, and when meeting summaries complete. Use these to build automated CRM updates, task creation workflows, and meeting analytics pipelines.

## Prerequisites
- Fireflies.ai account with API access (Business or Enterprise plan)
- Fireflies API key stored in `FIREFLIES_API_KEY` environment variable
- HTTPS endpoint for receiving webhook deliveries
- Understanding of Fireflies GraphQL API at `api.fireflies.ai/graphql`

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `Transcription completed` | Transcript ready | Meeting ID, transcript text, speakers |
| `Meeting started` | Bot joins meeting | Meeting ID, participants |
| `Meeting ended` | Bot leaves meeting | Meeting ID, duration |
| `Summary ready` | AI summary generated | Summary, action items, keywords |
| `Upload processed` | Audio file processed | Transcript ID, duration |

## Instructions

### Step 1: Register Webhook via GraphQL
```typescript
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

async function registerWebhook(url: string) {
  const mutation = `
    mutation AddWebhook($input: WebhookInput!) {
      addWebhook(input: $input) {
        id
        url
        events
        is_active
      }
    }
  `;

  const response = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({
      query: mutation,
      variables: {
        input: {
          url,
          events: ["Transcription completed", "Summary ready"],
          is_active: true,
        },
      },
    }),
  });

  return response.json();
}
```

### Step 2: Handle Transcript Events
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/fireflies", async (req, res) => {
  const { event_type, meeting_id, data } = req.body;
  res.status(200).json({ received: true });

  switch (event_type) {
    case "Transcription completed":
      await handleTranscriptReady(meeting_id, data);
      break;
    case "Summary ready":
      await handleSummaryReady(meeting_id, data);
      break;
  }
});

async function handleTranscriptReady(meetingId: string, data: any) {
  // Fetch full transcript via GraphQL
  const transcript = await fetchTranscript(meetingId);
  const { title, speakers, sentences, duration } = transcript;

  console.log(`Transcript ready: "${title}" (${duration}min, ${speakers.length} speakers)`);

  // Store transcript
  await db.transcripts.create({
    meetingId,
    title,
    speakers,
    sentences,
    duration,
    processedAt: new Date(),
  });
}
```

### Step 3: Fetch Full Transcript Data
```typescript
async function fetchTranscript(meetingId: string) {
  const query = `
    query GetTranscript($id: String!) {
      transcript(id: $id) {
        id
        title
        date
        duration
        speakers {
          name
          email
        }
        sentences {
          text
          speaker_name
          start_time
          end_time
        }
        summary {
          overview
          action_items
          keywords
        }
      }
    }
  `;

  const response = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query, variables: { id: meetingId } }),
  });

  const result = await response.json();
  return result.data.transcript;
}
```

### Step 4: Process Action Items
```typescript
async function handleSummaryReady(meetingId: string, data: any) {
  const transcript = await fetchTranscript(meetingId);
  const { summary } = transcript;

  // Create tasks from action items
  for (const item of summary.action_items) {
    await taskManager.createTask({
      title: item,
      source: `Meeting: ${transcript.title}`,
      meetingId,
      assignee: extractAssignee(item, transcript.speakers),
    });
  }

  // Send Slack digest
  await sendSlackDigest({
    title: transcript.title,
    overview: summary.overview,
    actionItems: summary.action_items,
    keywords: summary.keywords,
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Inactive webhook | Verify `is_active` via GraphQL query |
| Empty transcript | Short meeting | Minimum meeting duration required |
| Missing speakers | No calendar match | Ensure calendar integration is connected |
| Auth error on GraphQL | Invalid API key | Regenerate key in Fireflies dashboard |

## Examples

### Query Recent Transcripts
```bash
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ transcripts(limit: 5) { id title date duration } }"}'
```

## Resources
- [Fireflies API Documentation](https://docs.fireflies.ai/api)
- [Fireflies GraphQL Reference](https://docs.fireflies.ai/graphql)
- [Webhook Configuration](https://docs.fireflies.ai/webhooks)

## Next Steps
For deployment setup, see `fireflies-deploy-integration`.
