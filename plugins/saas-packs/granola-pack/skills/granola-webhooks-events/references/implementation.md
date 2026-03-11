# Granola Webhooks & Events - Implementation Details

## Event Payloads

### New Note Created
```json
{
  "event_type": "note.created",
  "timestamp": "2025-01-06T14:30:00Z",
  "data": {
    "note_id": "note_abc123",
    "meeting_title": "Sprint Planning",
    "meeting_date": "2025-01-06",
    "duration_minutes": 30,
    "attendees": [{"name": "Sarah Chen", "email": "sarah@company.com"}],
    "summary": "Discussed Q1 priorities...",
    "action_items": [{"text": "Review PRs", "assignee": "@mike", "due_date": "2025-01-08"}],
    "key_points": ["Agreed on feature freeze date"],
    "granola_url": "https://app.granola.ai/notes/note_abc123"
  }
}
```

### Note Updated
```json
{
  "event_type": "note.updated",
  "data": {
    "note_id": "note_abc123",
    "changes": {
      "summary": { "old": "Discussed...", "new": "Finalized..." },
      "action_items": { "added": [{"text": "New action"}], "removed": [] }
    },
    "updated_by": "user@company.com"
  }
}
```

## Custom Webhook Endpoint (Express.js)

```javascript
const express = require('express');
const app = express();
app.use(express.json());

app.post('/webhook/granola', (req, res) => {
  const event = req.body;
  console.log(`Received event: ${event.event_type}`);

  switch (event.event_type) {
    case 'note.created': handleNewNote(event.data); break;
    case 'note.updated': handleNoteUpdate(event.data); break;
  }
  res.status(200).json({ received: true });
});

async function handleNewNote(data) {
  for (const action of data.action_items) { await createTask(action); }
  await notifyTeam(data);
}
```

## Python Webhook Handler

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/granola', methods=['POST'])
def granola_webhook():
    event = request.json
    if event.get('event_type') == 'note.created':
        for action in event['data'].get('action_items', []):
            create_github_issue(action)
        post_to_slack(event['data'])
    return jsonify({'status': 'ok'}), 200
```

## Event Filtering

### Zapier Filters
```yaml
Filter by meeting type:
  meeting_title contains "sprint" OR "planning" OR attendees count > 3

Filter by content:
  summary contains "decision" OR action_items exists
```

### Code-Based Filtering
```javascript
const data = inputData;
if (!data.action_items || data.action_items.length === 0) return { skip: true };

const externalDomains = ['client.com', 'partner.org'];
const hasExternal = data.attendees.some(a => externalDomains.some(d => a.email.includes(d)));
if (!hasExternal) return { skip: true };

return { process: true, ...data };
```

## Processing Patterns

### Immediate Notification
Meeting Ends (T+0) -> Notes Ready (T+2 min) -> Webhook (T+2.1 min) -> Slack (T+2.2 min)
Total latency: ~2-3 minutes

### Batch Processing
Notes Created -> Queue -> Every 15 minutes: aggregate, generate digest, send single notification

### Conditional Routing
- If external attendee -> CRM Update
- If action items > 3 -> Create Project
- If duration > 60 min -> Request Summary
- Default -> Standard Processing

## Retry Logic
```javascript
async function processWithRetry(data, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await processEvent(data);
      return { success: true };
    } catch (error) {
      if (attempt === maxRetries) {
        await notifyError(data, error);
        return { success: false, error };
      }
      await sleep(Math.pow(2, attempt) * 1000); // Exponential backoff
    }
  }
}
```

## Monitoring Metrics
| Metric | Alert Threshold |
|--------|-----------------|
| Events/hour | > 100/hr |
| Processing latency | > 30 seconds |
| Error rate | > 5% |
| Queue depth | > 50 |
