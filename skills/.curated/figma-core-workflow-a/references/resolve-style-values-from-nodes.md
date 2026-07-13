# Step 2: Resolve Style Values from Nodes

Deep-dive reference for the `figma-core-workflow-a` skill — extracted from the 'Step 2: Resolve Style Values from Nodes' step of the workflow.

```typescript
// Fetch the actual nodes to get fill colors and text properties
const styleNodeIds = colorStyles.map(s => s.nodeId);
const nodesResponse = await client.getFileNodes(fileKey, styleNodeIds);

interface DesignToken {
  name: string;
  type: 'color' | 'typography' | 'spacing';
  value: string;
}

const tokens: DesignToken[] = [];

for (const [nodeId, nodeData] of Object.entries(nodesResponse.nodes)) {
  const node = nodeData.document;
  const styleName = colorStyles.find(s => s.nodeId === nodeId)?.name;

  if (node.fills?.[0]?.type === 'SOLID' && node.fills[0].color) {
    const { r, g, b, a } = node.fills[0].color;
    // Figma colors are 0-1 floats; convert to 0-255
    const hex = '#' + [r, g, b].map(v =>
      Math.round(v * 255).toString(16).padStart(2, '0')
    ).join('');

    tokens.push({
      name: styleName ?? node.name,
      type: 'color',
      value: a !== undefined && a < 1
        ? `rgba(${Math.round(r*255)}, ${Math.round(g*255)}, ${Math.round(b*255)}, ${a.toFixed(2)})`
        : hex,
    });
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
