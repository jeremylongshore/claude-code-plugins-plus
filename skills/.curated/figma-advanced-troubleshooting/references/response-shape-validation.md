# Step 2: Response Shape Validation

Deep-dive reference for the `figma-advanced-troubleshooting` skill — extracted from the 'Step 2: Response Shape Validation' step of the workflow.

```typescript
// Figma API responses can be unexpectedly shaped when:
// - File is empty or newly created
// - Nodes have been deleted between requests
// - Plugin data is corrupted

function validateFileResponse(data: any): string[] {
  const issues: string[] = [];

  if (!data.document) issues.push('Missing document root');
  if (!data.document?.children?.length) issues.push('Document has no pages');
  if (typeof data.name !== 'string') issues.push('Missing file name');
  if (!data.version) issues.push('Missing version field');

  // Check for null nodes (deleted between list and fetch)
  if (data.nodes) {
    for (const [id, node] of Object.entries(data.nodes)) {
      if (node === null) issues.push(`Null node: ${id} (deleted or invisible)`);
    }
  }

  // Check images response for null renders
  if (data.images) {
    for (const [id, url] of Object.entries(data.images)) {
      if (url === null) issues.push(`Image render failed for node: ${id}`);
    }
  }

  return issues;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
