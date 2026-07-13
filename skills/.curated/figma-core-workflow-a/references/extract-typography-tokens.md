# Step 3: Extract Typography Tokens

Deep-dive reference for the `figma-core-workflow-a` skill — extracted from the 'Step 3: Extract Typography Tokens' step of the workflow.

```typescript
// Fetch text style nodes
const textNodeIds = textStyles.map(s => s.nodeId);
const textNodes = await client.getFileNodes(fileKey, textNodeIds);

for (const [nodeId, nodeData] of Object.entries(textNodes.nodes)) {
  const node = nodeData.document;
  const styleName = textStyles.find(s => s.nodeId === nodeId)?.name;

  if (node.style) {
    tokens.push({
      name: styleName ?? node.name,
      type: 'typography',
      value: JSON.stringify({
        fontFamily: node.style.fontFamily,
        fontSize: `${node.style.fontSize}px`,
        fontWeight: node.style.fontWeight,
        lineHeight: node.style.lineHeightPx
          ? `${node.style.lineHeightPx}px`
          : 'normal',
        letterSpacing: node.style.letterSpacing
          ? `${node.style.letterSpacing}px`
          : '0',
      }),
    });
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
