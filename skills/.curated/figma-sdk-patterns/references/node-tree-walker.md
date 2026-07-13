# Step 4: Node Tree Walker

Deep-dive reference for the `figma-sdk-patterns` skill — extracted from the 'Step 4: Node Tree Walker' step of the workflow.

```typescript
// Walk the Figma document tree with a visitor pattern
function walkNodes(node: FigmaNode, visitor: (n: FigmaNode) => void) {
  visitor(node);
  if (node.children) {
    for (const child of node.children) {
      walkNodes(child, visitor);
    }
  }
}

// Example: find all TEXT nodes
function findTextNodes(root: FigmaNode): FigmaNode[] {
  const results: FigmaNode[] = [];
  walkNodes(root, (n) => {
    if (n.type === 'TEXT') results.push(n);
  });
  return results;
}

// Example: find all COMPONENT nodes
function findComponents(root: FigmaNode): FigmaNode[] {
  const results: FigmaNode[] = [];
  walkNodes(root, (n) => {
    if (n.type === 'COMPONENT') results.push(n);
  });
  return results;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
