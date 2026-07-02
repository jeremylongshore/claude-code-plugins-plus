# Step 3: Export All Icons from a Frame

Deep-dive reference for the `figma-core-workflow-b` skill — extracted from the 'Step 3: Export All Icons from a Frame' step of the workflow.

```typescript
// Find all COMPONENT children in an "Icons" frame, then export each as SVG
async function exportIconsFromFrame(frameNodeId: string) {
  // Fetch the frame and its children
  const res = await fetch(
    `https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${frameNodeId}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();
  const frame = data.nodes[frameNodeId]?.document;

  if (!frame?.children) throw new Error('Frame has no children');

  // Collect component node IDs
  const iconIds = frame.children
    .filter((n: any) => n.type === 'COMPONENT' || n.type === 'INSTANCE')
    .map((n: any) => n.id);

  console.log(`Found ${iconIds.length} icons to export`);

  // Export as SVG (batch -- up to 100 IDs per request)
  const batchSize = 100;
  for (let i = 0; i < iconIds.length; i += batchSize) {
    const batch = iconIds.slice(i, i + batchSize);
    await downloadAssets(batch, './assets/icons', 'svg');
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
