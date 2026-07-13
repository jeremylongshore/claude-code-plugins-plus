# Step 2: Extract Styles from Source

Deep-dive reference for the `figma-migration-deep-dive` skill — extracted from the 'Step 2: Extract Styles from Source' step of the workflow.

```typescript
async function extractAllStyles(fileKey: string) {
  const file = await fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const styleNodeIds = Object.keys(file.styles);
  const nodesRes = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${styleNodeIds.join(',')}`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const extracted = [];
  for (const [nodeId, styleMeta] of Object.entries(file.styles) as any[]) {
    const node = nodesRes.nodes[nodeId]?.document;
    if (!node) continue;

    extracted.push({
      name: styleMeta.name,
      type: styleMeta.style_type,
      nodeId,
      data: {
        fills: node.fills,
        strokes: node.strokes,
        effects: node.effects,
        style: node.style,       // typography
        characters: node.characters,
      },
    });
  }

  return extracted;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
