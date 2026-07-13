# Step 3: Manage Webhooks

Deep-dive reference for the `figma-webhooks-events` skill — extracted from the 'Step 3: Manage Webhooks' step of the workflow.

```typescript
const FIGMA_API = 'https://api.figma.com';

// List all webhooks for a team
async function listWebhooks(teamId: string) {
  const res = await fetch(`${FIGMA_API}/v2/webhooks?team_id=${teamId}`, {
    headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
  });
  return res.json(); // { webhooks: [...] }
}

// Delete a webhook
async function deleteWebhook(webhookId: string) {
  await fetch(`${FIGMA_API}/v2/webhooks/${webhookId}`, {
    method: 'DELETE',
    headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
  });
}

// Update a webhook (e.g., change endpoint)
async function updateWebhook(webhookId: string, updates: Record<string, any>) {
  const res = await fetch(`${FIGMA_API}/v2/webhooks/${webhookId}`, {
    method: 'PUT',
    headers: {
      'X-Figma-Token': process.env.FIGMA_PAT!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  return res.json();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
