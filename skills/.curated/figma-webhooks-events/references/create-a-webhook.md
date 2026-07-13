# Step 1: Create a Webhook

Deep-dive reference for the `figma-webhooks-events` skill — extracted from the 'Step 1: Create a Webhook' step of the workflow.

```bash
# POST /v2/webhooks -- requires webhooks:write scope
curl -X POST https://api.figma.com/v2/webhooks \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_UPDATE",
    "team_id": "123456789",
    "endpoint": "https://yourapp.com/webhooks/figma",
    "passcode": "your-secret-passcode",
    "description": "Sync design tokens on file update"
  }'

# Response:
# { "id": "wh_abc123", "event_type": "FILE_UPDATE", "status": "ACTIVE", ... }
```

**Available event types:**

| Event Type | Trigger | Payload Contains |
|------------|---------|-----------------|
| `FILE_UPDATE` | File saved to version history | `file_key`, `file_name`, `timestamp` |
| `FILE_DELETE` | File deleted | `file_key`, `file_name` |
| `FILE_VERSION_UPDATE` | Named version created | `file_key`, `version_id`, `label` |
| `FILE_COMMENT` | Comment added | `file_key`, `comment`, `comment_id` |
| `LIBRARY_PUBLISH` | Library published | `file_key`, `description`, variables |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
