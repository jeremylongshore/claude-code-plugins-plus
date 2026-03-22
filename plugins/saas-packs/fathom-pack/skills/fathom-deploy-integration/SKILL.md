---
name: fathom-deploy-integration
description: |
  Deploy Fathom webhook handlers and meeting sync services.
  Trigger with phrases like "deploy fathom", "fathom webhook server", "fathom cloud function".
allowed-tools: Read, Write, Edit, Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Deploy Integration

## Webhook Handler (Cloud Function)

```python
import functions_framework
from fathom_client import FathomClient

@functions_framework.http
def fathom_webhook(request):
    event = request.get_json()
    event_type = event.get("type")

    if event_type == "meeting_content_ready":
        recording_id = event["recording_id"]
        client = FathomClient()
        transcript = client.get_transcript(recording_id)
        summary = client.get_summary(recording_id)
        # Process and sync to CRM/database
        return {"status": "processed"}

    return {"status": "ignored"}
```

```bash
gcloud functions deploy fathom-webhook \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --set-secrets=FATHOM_API_KEY=fathom-api-key:latest
```

## Resources

- [Fathom Webhooks](https://developers.fathom.ai/webhooks)

## Next Steps

For webhook setup, see `fathom-webhooks-events`.
