# Step 4: Named Export with Component Metadata

Deep-dive reference for the `figma-core-workflow-b` skill — extracted from the 'Step 4: Named Export with Component Metadata' step of the workflow.

```typescript
// Use component metadata for better filenames
async function exportNamedIcons(frameNodeId: string) {
  const fileRes = await fetch(
    `https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${frameNodeId}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const fileData = await fileRes.json();
  const frame = fileData.nodes[frameNodeId].document;

  // Build nodeId -> name map
  const nameMap = new Map<string, string>();
  for (const child of frame.children ?? []) {
    const safeName = child.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    nameMap.set(child.id, safeName);
  }

  // Export
  const nodeIds = Array.from(nameMap.keys());
  const imageUrls = await exportImages(nodeIds, 'svg');

  mkdirSync('./assets/icons', { recursive: true });
  for (const [nodeId, url] of Object.entries(imageUrls)) {
    if (!url) continue;
    const name = nameMap.get(nodeId) ?? nodeId.replace(':', '-');
    const res = await fetch(url);
    const svg = await res.text();
    writeFileSync(`./assets/icons/${name}.svg`, svg);
    console.log(`Exported: ${name}.svg`);
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
