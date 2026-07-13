# Step 2: Webhooks V1 to V2 Migration

Deep-dive reference for the `figma-upgrade-migration` skill — extracted from the 'Step 2: Webhooks V1 to V2 Migration' step of the workflow.

```typescript
// V1 (deprecated): POST /v1/webhooks
// V2 (current):    POST /v2/webhooks

// V2 adds context support: attach webhooks to teams, files, or projects
interface WebhookV2Config {
  event_type: 'FILE_UPDATE' | 'FILE_DELETE' | 'FILE_VERSION_UPDATE'
    | 'FILE_COMMENT' | 'LIBRARY_PUBLISH';
  // Context: where to listen
  team_id?: string;      // team-level (all files in team)
  // OR specify project/file context in the endpoint path
  endpoint: string;      // Your HTTPS webhook URL
  passcode: string;      // Secret for verification
  description?: string;
}

// Create a V2 webhook
async function createWebhook(config: WebhookV2Config) {
  const res = await fetch('https://api.figma.com/v2/webhooks', {
    method: 'POST',
    headers: {
      'X-Figma-Token': process.env.FIGMA_PAT!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error(`Webhook creation failed: ${res.status}`);
  return res.json();
}

// List existing webhooks
async function listWebhooks(teamId: string) {
  const res = await fetch(
    `https://api.figma.com/v2/webhooks?team_id=${teamId}`,
    { headers: { 'X-Figma-Token': process.env.FIGMA_PAT! } }
  );
  return res.json();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
