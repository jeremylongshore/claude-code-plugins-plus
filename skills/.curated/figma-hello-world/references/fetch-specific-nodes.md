# Step 4: Fetch Specific Nodes

Deep-dive reference for the `figma-hello-world` skill — extracted from the 'Step 4: Fetch Specific Nodes' step of the workflow.

```typescript
// Fetch only specific nodes by ID (faster for large files)
async function fetchNodes(fileKey: string, nodeIds: string[]) {
  const ids = nodeIds.join(',');
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();
  // data.nodes is a map: { "nodeId": { document: {...}, components: {...} } }
  return data.nodes;
}

// Node IDs use the format "pageId:frameId" (e.g., "0:1", "123:456")
const nodes = await fetchNodes(FILE_KEY, ['0:1', '2:3']);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
