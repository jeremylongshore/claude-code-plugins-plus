# Apify Webhooks — Payload Templates & Local Testing

Reference material for the payload template variables Apify exposes and for
exercising a webhook endpoint locally before you point production Actors at it.

## Webhook Payload Template Variables

| Variable | Description |
|----------|-------------|
| `{{eventType}}` | Event type string |
| `{{eventData}}` | Full event data object |
| `{{createdAt}}` | Event creation timestamp |
| `{{actorId}}` | Actor ID |
| `{{actorRunId}}` | Run ID |
| `{{actorTaskId}}` | Task ID (if run from a task) |
| `{{resource.*}}` | Any field from the run object |

## Ad-Hoc Webhook via REST API (curl)

Attach a webhook to a single run when starting it through the REST API:

```bash
curl -X POST \
  "https://api.apify.com/v2/acts/USERNAME~ACTOR_NAME/runs" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "startUrls": [{"url": "https://example.com"}],
    "webhooks": [
      {
        "eventTypes": ["ACTOR.RUN.SUCCEEDED"],
        "requestUrl": "https://your-app.com/webhook"
      }
    ]
  }'
```

## Testing Webhooks Locally

```bash
# Use ngrok to expose local server
ngrok http 3000
# Copy the HTTPS URL

# Create a test webhook pointing to ngrok
# Then trigger a run to see the webhook fire

# Or manually simulate a webhook payload
curl -X POST http://localhost:3000/api/webhooks/apify \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorRunId": "test-run-123",
    "defaultDatasetId": "test-dataset-456",
    "status": "SUCCEEDED"
  }'
```
