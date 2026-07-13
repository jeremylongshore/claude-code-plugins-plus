# Step 3: Reduce API Calls

Deep-dive reference for the `figma-cost-tuning` skill — extracted from the 'Step 3: Reduce API Calls' step of the workflow.

```typescript
// 1. Use depth parameter to avoid fetching full file trees
// Saves bandwidth and processing time
const fileMeta = await figmaFetch(`/v1/files/${key}?depth=1`);

// 2. Batch node IDs into single requests
// Instead of 50 individual /nodes calls, make 1 call with 50 IDs
const ids = nodeIds.join(',');
await figmaFetch(`/v1/files/${key}/nodes?ids=${ids}`);

// 3. Cache with webhooks instead of polling
// Polling every 30s = 2,880 calls/day per file
// Webhooks = 0 polling calls (events push to you)

// 4. Cache image URLs (they're valid for 30 days)
// Re-rendering the same nodes wastes Tier 1 quota

// 5. Use GET /v1/files/:key?depth=1 to check lastModified
// before fetching the full file (skip if unchanged)
async function fetchFileIfChanged(
  fileKey: string,
  lastKnownVersion: string,
  token: string
) {
  const meta = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  if (meta.version === lastKnownVersion) {
    console.log('File unchanged, skipping full fetch');
    return null;
  }

  // File changed -- fetch the full version
  return fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
