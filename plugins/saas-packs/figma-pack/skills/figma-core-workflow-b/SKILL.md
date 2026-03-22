---
name: figma-core-workflow-b
description: |
  Export images, icons, and assets from Figma files via the REST API.
  Use when building an asset pipeline, exporting icons as SVG/PNG,
  or rendering frames to images for documentation or previews.
  Trigger with phrases like "figma export", "figma images",
  "export figma icons", "figma assets", "figma render".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Core Workflow B -- Asset Export

## Overview
Export images, icons, and assets from Figma files using the REST API. Render specific nodes as PNG, SVG, JPG, or PDF. Build automated asset pipelines for icons, illustrations, and component previews.

## Prerequisites
- Completed `figma-install-auth` setup
- Node IDs of the frames/components to export (from `figma-hello-world`)
- `FIGMA_PAT` and `FIGMA_FILE_KEY` env vars set

## Instructions

### Step 1: Render Nodes as Images
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

### Step 2: Download Exported Images
```typescript
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

async function downloadAssets(
  nodeIds: string[],
  outputDir: string,
  format: 'png' | 'svg' = 'svg'
) {
  mkdirSync(outputDir, { recursive: true });

  const imageUrls = await exportImages(nodeIds, format);
  const results: { nodeId: string; path: string; success: boolean }[] = [];

  for (const [nodeId, url] of Object.entries(imageUrls)) {
    if (!url) {
      console.warn(`Node ${nodeId}: render returned null (invisible or invalid)`);
      results.push({ nodeId, path: '', success: false });
      continue;
    }

    const res = await fetch(url);
    const buffer = Buffer.from(await res.arrayBuffer());
    const filename = `${nodeId.replace(':', '-')}.${format}`;
    const filepath = join(outputDir, filename);
    writeFileSync(filepath, buffer);
    results.push({ nodeId, path: filepath, success: true });
  }

  return results;
}
```

### Step 3: Export All Icons from a Frame
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

### Step 4: Named Export with Component Metadata
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

## Output
- Images rendered from Figma nodes at specified format and scale
- Downloaded assets saved to local filesystem
- Icon library exported as named SVG files
- Batch processing for large component sets

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `null` in images map | Node is invisible or has 0% opacity | Make node visible in Figma |
| 400 Bad Request | Invalid node ID format | Use `pageId:nodeId` format (e.g., `0:1`) |
| 429 Rate Limited | Images endpoint is Tier 1 | Batch requests, honor `Retry-After` |
| Image URL expired | URLs expire after 30 days | Re-export; do not cache URLs long-term |
| SVG has `scale` > 1 | SVG ignores scale param | SVG always exports at 1x |

## Examples

### Quick Export via curl
```bash
# Export a single node as PNG at 2x
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/images/${FIGMA_FILE_KEY}?ids=0:1&format=png&scale=2" \
  | jq -r '.images["0:1"]'
# Returns a temporary URL to the rendered image
```

## Resources
- [Figma Images Endpoint](https://developers.figma.com/docs/rest-api/file-endpoints/)
- [Export Settings](https://developers.figma.com/docs/plugins/api/ExportSettings/)
- [figma-export-assets](https://github.com/mariohamann/figma-export-assets) (community tool)

## Next Steps
For common errors, see `figma-common-errors`.
