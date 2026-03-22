---
name: fathom-webhooks-events
description: |
  Configure Fathom webhooks for real-time meeting notifications.
  Use when setting up automated meeting processing, receiving real-time
  transcripts, or triggering workflows when meetings complete.
  Trigger with phrases like "fathom webhook", "fathom notifications",
  "fathom real-time", "fathom event handler".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Webhooks & Events

## Overview

Fathom webhooks send meeting data to your URL when recordings are ready. Webhooks can include summary, transcript, and action items. Configure in Settings or via API.

## Webhook Setup

### Via API

```bash
curl -X POST -H "X-Api-Key: ${FATHOM_API_KEY}" \
  -H "Content-Type: application/json" \
  https://api.fathom.ai/external/v1/webhooks \
  -d '{
    "url": "https://your-app.com/webhooks/fathom",
    "include_summary": true,
    "include_transcript": true,
    "include_action_items": true,
    "fire_on_own_meetings": true,
    "fire_on_shared_meetings": false
  }'
```

### Via Settings

Navigate to Settings > Integrations > Webhooks > Create Webhook.

## Webhook Payload

```json
{
  "type": "meeting_content_ready",
  "recording_id": "rec-abc123",
  "url": "https://fathom.video/call/abc123",
  "share_url": "https://fathom.video/share/abc123",
  "title": "Product Review Q1",
  "summary": "Discussed roadmap priorities...",
  "transcript": [...],
  "action_items": [...]
}
```

## Webhook Handler

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhooks/fathom", methods=["POST"])
def fathom_webhook():
    event = request.json
    if event.get("type") == "meeting_content_ready":
        recording_id = event["recording_id"]
        summary = event.get("summary", "")
        actions = event.get("action_items", [])
        # Process meeting data
        print(f"Meeting ready: {event.get('title')} ({len(actions)} action items)")
    return jsonify({"received": True}), 200
```

## Testing Webhooks

```bash
# Test with webhook.site
curl -X POST https://webhook.site/your-uuid \
  -H "Content-Type: application/json" \
  -d '{"type": "meeting_content_ready", "recording_id": "test"}'

# Or use ngrok for local testing
ngrok http 5000
```

## Resources

- [Fathom Webhooks](https://developers.fathom.ai/webhooks)
- [Webhook Troubleshooting](https://help.fathom.video/en/articles/10625473)

## Next Steps

For performance optimization, see `fathom-performance-tuning`.
