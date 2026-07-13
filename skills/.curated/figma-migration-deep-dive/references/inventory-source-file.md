# Step 1: Inventory Source File

Deep-dive reference for the `figma-migration-deep-dive` skill — extracted from the 'Step 1: Inventory Source File' step of the workflow.

```typescript
const PAT = process.env.FIGMA_PAT!;

async function inventoryFile(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const file = await res.json();

  const inventory = {
    name: file.name,
    pages: file.document.children.map((p: any) => p.name),
    componentCount: Object.keys(file.components).length,
    styleCount: Object.keys(file.styles).length,
    styles: {
      fills: Object.values(file.styles).filter((s: any) => s.style_type === 'FILL').length,
      text: Object.values(file.styles).filter((s: any) => s.style_type === 'TEXT').length,
      effects: Object.values(file.styles).filter((s: any) => s.style_type === 'EFFECT').length,
      grids: Object.values(file.styles).filter((s: any) => s.style_type === 'GRID').length,
    },
  };

  // Count total nodes
  let nodeCount = 0;
  function countNodes(node: any) {
    nodeCount++;
    if (node.children) node.children.forEach(countNodes);
  }
  countNodes(file.document);
  (inventory as any).totalNodes = nodeCount;

  return inventory;
}

// Usage
const inv = await inventoryFile(process.env.FIGMA_FILE_KEY!);
console.log(`File: ${inv.name}`);
console.log(`Pages: ${inv.pages.join(', ')}`);
console.log(`Components: ${inv.componentCount}, Styles: ${inv.styleCount}`);
console.log(`Total nodes: ${(inv as any).totalNodes}`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
