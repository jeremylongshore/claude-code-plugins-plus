# Step 4: Batch Node Fetches

Deep-dive reference for the `figma-performance-tuning` skill — extracted from the 'Step 4: Batch Node Fetches' step of the workflow.

```typescript
// The /nodes endpoint accepts multiple IDs -- batch them
// Max practical batch size: ~50-100 IDs per request

async function batchFetchNodes(
  fileKey: string,
  nodeIds: string[],
  token: string,
  batchSize = 50
): Promise<Map<string, any>> {
  const results = new Map<string, any>();

  for (let i = 0; i < nodeIds.length; i += batchSize) {
    const batch = nodeIds.slice(i, i + batchSize);
    const ids = encodeURIComponent(batch.join(','));

    const data = await fetch(
      `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`,
      { headers: { 'X-Figma-Token': token } }
    ).then(r => r.json());

    for (const [id, node] of Object.entries(data.nodes)) {
      results.set(id, node);
    }
  }

  return results;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
