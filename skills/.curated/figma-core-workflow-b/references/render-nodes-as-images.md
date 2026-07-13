# Step 1: Render Nodes as Images

Deep-dive reference for the `figma-core-workflow-b` skill — extracted from the 'Step 1: Render Nodes as Images' step of the workflow.

```typescript
const PAT = process.env.FIGMA_PAT!;
const FILE_KEY = process.env.FIGMA_FILE_KEY!;

// GET /v1/images/:file_key?ids=X,Y&format=png&scale=2
// Supported formats: png, svg, jpg, pdf
// Scale: 0.01 to 4 (SVG always exports at 1x)
// Max image size: 32 megapixels (larger images are auto-scaled down)
async function exportImages(
  nodeIds: string[],
  format: 'png' | 'svg' | 'jpg' | 'pdf' = 'png',
  scale = 2
): Promise<Record<string, string | null>> {
  const params = new URLSearchParams({
    ids: nodeIds.join(','),
    format,
    scale: String(format === 'svg' ? 1 : scale), // SVG is always 1x
  });

  const res = await fetch(
    `https://api.figma.com/v1/images/${FILE_KEY}?${params}`,
    { headers: { 'X-Figma-Token': PAT } }
  );

  if (!res.ok) throw new Error(`Image export failed: ${res.status}`);
  const data = await res.json();

  // data.images: { "nodeId": "https://..." | null }
  // null means the node failed to render (invisible, 0% opacity, or invalid ID)
  // URLs expire after 30 days
  return data.images;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
