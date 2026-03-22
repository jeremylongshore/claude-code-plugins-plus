---
name: adobe-export-assets
description: |
  Execute Adobe primary workflow: Export & Asset Pipeline.
  Use when exporting icons and images for a web build pipeline,
  generating PDFs from design presentations, or syncing design tokens to CSS variables.
  Trigger with phrases like "adobe export assets",
  "export design assets with adobe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, adobe]
---

# Adobe Export & Asset Pipeline

## Overview
Export design assets (images, SVGs, PDFs) from design files programmatically.
This is the primary integration workflow — bridging design to code.


## Prerequisites
- Completed `adobe-install-auth` setup

- Understanding of Adobe core concepts

- Valid API credentials configured

## Instructions

### Step 1: Select File and Components
```typescript
const file = await client.files.get(fileId);
const components = file.document.children
  .filter(node => node.type === 'COMPONENT')
  .map(c => ({ id: c.id, name: c.name }));
console.log(`Found ${components.length} exportable components`);

```

### Step 2: Request Export Renders
```typescript
const exports = await client.files.export(fileId, {
  ids: components.map(c => c.id),
  format: 'svg', // svg, png, pdf, jpg
  scale: 2,      // 2x for retina
});
// Returns { images: { [nodeId]: downloadUrl } }

```

### Step 3: Download and Save Assets
```typescript
for (const [nodeId, url] of Object.entries(exports.images)) {
  const name = components.find(c => c.id === nodeId)?.name || nodeId;
  const response = await fetch(url);
  const buffer = await response.arrayBuffer();
  fs.writeFileSync(`assets/${name}.svg`, Buffer.from(buffer));
  console.log(`Exported: ${name}.svg`);
}

```

## Output
- Completed Export & Asset Pipeline execution

- Expected results from Adobe API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| File Not Found | Invalid file ID or file was deleted/moved | Verify file ID from the file URL. Check if file was moved to another project. |
| Export Timeout | File too complex or too many nodes requested at once | Reduce export batch size. Export individual pages instead of full file. |

## Examples

### Complete Workflow
```typescript
// Full asset export pipeline
const client = new DesignClient({ accessToken: process.env.ACCESS_TOKEN });

async function exportAssets(fileId: string, format = 'svg') {
  const file = await client.files.get(fileId);
  const nodes = file.document.children.filter(n => n.exportSettings?.length > 0);
  const exports = await client.files.export(fileId, {
    ids: nodes.map(n => n.id),
    format,
    scale: 2,
  });
  return exports.images;
}

```

### Common Variations
- **SVG for icons**: `format: 'svg'` for infinitely scalable vector icons
- **PNG for images**: `format: 'png', scale: 2` for retina-ready rasters
- **PDF for print**: `format: 'pdf'` for print-ready exports


## Resources
- [Adobe Documentation](https://docs.adobe.com)
- [Adobe API Reference](https://docs.adobe.com/api)

## Next Steps
For secondary workflow, see `adobe-design-token-sync`.