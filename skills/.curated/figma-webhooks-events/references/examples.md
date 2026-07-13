# figma-webhooks-events: Worked Examples

Worked examples for the `figma-webhooks-events` skill — extracted from the skill's Examples section.

## Test Webhook Locally

```bash
# Use ngrok to expose local server
ngrok http 3000

# Create webhook pointing to ngrok URL
curl -X POST https://api.figma.com/v2/webhooks \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_UPDATE",
    "team_id": "YOUR_TEAM_ID",
    "endpoint": "https://YOUR-NGROK.ngrok.io/webhooks/figma",
    "passcode": "test-passcode"
  }'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
