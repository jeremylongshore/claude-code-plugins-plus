---
name: granola-webhooks-events
description: |
  Build event-driven automations with Granola's Zapier webhook triggers.
  Use when creating real-time notification systems, processing meeting events,
  or building custom integrations that react to Granola note creation.
  Trigger: "granola webhooks", "granola events", "granola triggers",
  "granola real-time", "granola event-driven".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, webhooks, automation]

---
# Granola Webhooks & Events

## Overview
Granola does not expose raw webhook endpoints. All event-driven automation flows through Zapier, which provides two trigger events. This skill covers the event model, webhook payload structure, event filtering, processing patterns, and building custom event handlers.

## Prerequisites
- Granola Business plan (for Zapier access)
- Zapier account (Free for basic Zaps, Paid for multi-step)
- Optional: custom webhook endpoint (Express.js, FastAPI, or serverless function)

## Instructions

### Step 1 — Understand the Event Model

Granola fires events through Zapier triggers, not direct webhooks. Two triggers are available:

| Trigger | When It Fires | Use Case |
|---------|--------------|----------|
| **Note Added to Granola Folder** | A note is placed in a specific folder (automatic) | Auto-route by meeting type |
| **Note Shared to Zapier** | You manually click Share > Zapier on a note | Selective sharing for important meetings |

### Step 2 — Webhook Payload Structure

When a Zapier trigger fires, Granola sends this data:

```json
{
  "title": "Sprint Planning — Q1 Week 12",
  "creator_name": "Sarah Chen",
  "creator_email": "sarah@company.com",
  "attendees": [
    {"name": "Sarah Chen", "email": "sarah@company.com"},
    {"name": "Mike Johnson", "email": "mike@company.com"},
    {"name": "Alex Kim", "email": "alex@external.com"}
  ],
  "calendar_event_title": "Sprint Planning",
  "calendar_event_datetime": "2026-03-22T10:00:00Z",
  "note_content": "## Summary\nDiscussed Q1 priorities...\n\n## Action Items\n- [ ] @sarah: Schedule design review..."
}
```

**Key fields for filtering and routing:**
- `attendees[].email` — detect internal vs. external meetings
- `calendar_event_title` — match meeting type patterns
- `note_content` — search for action items, decisions, keywords

### Step 3 — Event Filtering Patterns

Use Zapier Filter steps to route events:

**Filter: Only External Meetings**
```
Filter: attendees.email DOES NOT contain "@company.com"
(at least one attendee has a non-company email)
```

**Filter: Only Meetings with Action Items**
```
Filter: note_content contains "- [ ]"
```

**Filter: Only Sales Calls (by title keywords)**
```
Filter: calendar_event_title contains any of: "discovery", "demo", "sales", "prospect"
```

**Filter: Long Meetings Only (> 30 min)**
```
Use Zapier Code step to parse calendar_event_datetime and compare to note timestamp
```

### Step 4 — Build a Custom Webhook Handler

Forward Granola events from Zapier to your own endpoint:

```yaml
# Zapier configuration
Trigger: Granola — Note Added to Folder ("All Meetings")
Action: Webhooks by Zapier — POST
  URL: https://your-api.com/webhooks/granola
  Payload Type: JSON
  Data:
    title: "{{title}}"
    creator: "{{creator_email}}"
    attendees: "{{attendees}}"
    content: "{{note_content}}"
    datetime: "{{calendar_event_datetime}}"
    hmac: "{{your_webhook_secret}}"
```

**Express.js handler:**
```javascript
// webhook-handler.js
import express from 'express';
const app = express();
app.use(express.json());

app.post('/webhooks/granola', async (req, res) => {
  const { title, creator, attendees, content, datetime } = req.body;

  // Validate webhook (use HMAC or shared secret)
  // if (!verifyHmac(req)) return res.status(401).send('Unauthorized');

  console.log(`Meeting received: ${title} (${datetime})`);

  // Extract action items
  const actionItems = content
    .split('\n')
    .filter(line => line.match(/^- \[ \]/))
    .map(line => line.replace('- [ ] ', ''));

  // Route based on meeting type
  const isExternal = attendees.some(a => !a.email?.endsWith('@company.com'));

  if (isExternal) {
    await handleExternalMeeting({ title, attendees, content, actionItems });
  } else {
    await handleInternalMeeting({ title, content, actionItems });
  }

  res.status(200).json({ processed: true, actions: actionItems.length });
});

async function handleExternalMeeting({ title, attendees, content, actionItems }) {
  // CRM update, follow-up email draft, Slack #sales notification
  console.log(`External meeting: ${title}, ${actionItems.length} action items`);
}

async function handleInternalMeeting({ title, content, actionItems }) {
  // Linear tasks, Notion archive, Slack #team notification
  console.log(`Internal meeting: ${title}, ${actionItems.length} action items`);
}

app.listen(3000, () => console.log('Granola webhook handler running on :3000'));
```

**Python FastAPI handler:**
```python
from fastapi import FastAPI, Request
import re

app = FastAPI()

@app.post("/webhooks/granola")
async def handle_granola_event(request: Request):
    data = await request.json()
    title = data.get("title", "Untitled")
    content = data.get("content", "")
    attendees = data.get("attendees", [])

    # Extract action items
    actions = re.findall(r"- \[ \] (.+)", content)

    # Route by attendee type
    external = [a for a in attendees if not a.get("email", "").endswith("@company.com")]

    if external:
        # Process external meeting
        await process_external(title, actions, external)
    else:
        await process_internal(title, actions)

    return {"processed": True, "action_count": len(actions)}
```

### Step 5 — Processing Patterns

| Pattern | When to Use | Implementation |
|---------|------------|----------------|
| **Immediate** | Time-sensitive follow-ups | Direct Zapier actions, ~2 min latency |
| **Batch** | Reduce noise, aggregate | Queue to SQS/Redis, process every 15 min |
| **Conditional** | Route by meeting type | Zapier Paths or custom webhook with routing logic |
| **Idempotent** | Prevent duplicate processing | Store processed note IDs, skip duplicates |

### Step 6 — Error Handling and Retry

Zapier handles retries automatically for failed actions. For custom webhooks:

```javascript
// Implement idempotency
const processedNotes = new Set(); // Use Redis/DB in production

app.post('/webhooks/granola', async (req, res) => {
  const noteId = `${req.body.title}-${req.body.datetime}`;

  if (processedNotes.has(noteId)) {
    return res.status(200).json({ status: 'already_processed' });
  }

  processedNotes.add(noteId);
  // ... process the event
});
```

## Output
- Zapier triggers configured for target folders
- Event filtering routing meetings by type
- Custom webhook handler processing events
- Idempotency preventing duplicate processing

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Trigger not firing | Wrong folder name in Zapier | Verify folder name matches exactly (case-sensitive) |
| Empty note_content | Note still processing when trigger fires | Add 2-minute Delay step before processing actions |
| Duplicate events | Zapier retry on timeout | Implement idempotency with note ID deduplication |
| Webhook timeout | Handler takes > 30s | Return 200 immediately, process async |
| Missing attendees | Calendar event has no attendee list | No fix — attendees come from calendar event data |

## Resources
- [Zapier Granola Integration](https://zapier.com/apps/granola/integrations)
- [Zapier Webhooks Documentation](https://zapier.com/help/create/code-webhooks)
- [4 Ways to Automate Granola](https://zapier.com/blog/automate-granola/)

## Next Steps
Proceed to `granola-performance-tuning` for transcription quality optimization.
