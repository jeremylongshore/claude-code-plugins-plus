# Step 5: Batch Node Requests

Deep-dive reference for the `figma-rate-limits` skill — extracted from the 'Step 5: Batch Node Requests' step of the workflow.

```typescript
// Instead of N individual /v1/files/:key/nodes requests,
// batch node IDs into fewer requests
async function batchFetchNodes(
  fileKey: string,
  nodeIds: string[],
  batchSize = 50,
  token: string
) {
  const results: Record<string, any> = {};

  for (let i = 0; i < nodeIds.length; i += batchSize) {
    const batch = nodeIds.slice(i, i + batchSize);
    const ids = encodeURIComponent(batch.join(','));
    const data = await queuedFigmaRequest(
      `/v1/files/${fileKey}/nodes?ids=${ids}`,
      token
    );
    Object.assign(results, data.nodes);
  }

  return results;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
