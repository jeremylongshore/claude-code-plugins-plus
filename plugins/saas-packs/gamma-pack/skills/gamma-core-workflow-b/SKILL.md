---
name: gamma-core-workflow-b
description: |
  Implement core Gamma workflow for presentation editing and export.
  Use when modifying existing presentations, exporting to various formats,
  or managing presentation assets.
  Trigger with phrases like "gamma edit presentation", "gamma export",
  "gamma PDF", "gamma update slides", "gamma modify".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Core Workflow B: Editing and Export

## Overview
Implement workflows for editing existing presentations and exporting to various formats.

## Prerequisites
- Completed `gamma-core-workflow-a` setup
- Existing presentation to work with
- Understanding of export formats

## Instructions

### Step 1: Retrieve and Edit Presentation
```typescript
import { GammaClient } from '@gamma/sdk';

const gamma = new GammaClient({ apiKey: process.env.GAMMA_API_KEY });

async function editPresentation(presentationId: string) {
  // Retrieve existing presentation
  const presentation = await gamma.presentations.get(presentationId);

  // Update title and style
  const updated = await gamma.presentations.update(presentationId, {
    title: 'Updated: ' + presentation.title,
    style: 'modern',
  });

  return updated;
}
```

### Step 2: Slide-Level Editing
```typescript
async function editSlide(presentationId: string, slideIndex: number, content: object) {
  const presentation = await gamma.presentations.get(presentationId);

  // Update specific slide
  const updatedSlide = await gamma.slides.update(
    presentationId,
    slideIndex,
    {
      title: content.title,
      content: content.body,
      layout: content.layout || 'content',
    }
  );

  return updatedSlide;
}

async function addSlide(presentationId: string, position: number, content: object) {
  return gamma.slides.insert(presentationId, position, {
    title: content.title,
    content: content.body,
    generateImage: content.imagePrompt,
  });
}

async function deleteSlide(presentationId: string, slideIndex: number) {
  return gamma.slides.delete(presentationId, slideIndex);
}
```

### Step 3: Export to Various Formats
```typescript
type ExportFormat = 'pdf' | 'pptx' | 'png' | 'html';

async function exportPresentation(
  presentationId: string,
  format: ExportFormat,
  options: object = {}
) {
  const exportJob = await gamma.exports.create(presentationId, {
    format,
    quality: options.quality || 'high',
    includeNotes: options.includeNotes ?? true,
    ...options,
  });

  // Wait for export to complete
  const result = await gamma.exports.wait(exportJob.id, {
    timeout: 60000,  # 60000: 1 minute in ms
    pollInterval: 2000,  # 2000: 2 seconds in ms
  });

  return result.downloadUrl;
}

// Usage examples
const pdfUrl = await exportPresentation('pres-123', 'pdf');
const pptxUrl = await exportPresentation('pres-123', 'pptx', { includeNotes: false });
const pngUrl = await exportPresentation('pres-123', 'png', { slideIndex: 0 }); // First slide only
```

### Step 4: Asset Management
```typescript
async function uploadAsset(presentationId: string, filePath: string) {
  const fileBuffer = await fs.readFile(filePath);

  const asset = await gamma.assets.upload(presentationId, {
    file: fileBuffer,
    filename: path.basename(filePath),
    type: 'image',
  });

  return asset.url;
}

async function listAssets(presentationId: string) {
  return gamma.assets.list(presentationId);
}
```

## Output
- Updated presentation with modifications
- Exported files in various formats
- Managed presentation assets
- Download URLs for exports

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Export Timeout | Large presentation | Increase timeout or reduce slides |
| Format Not Supported | Invalid export format | Check supported formats |
| Asset Too Large | File exceeds limit | Compress or resize image |
| Slide Not Found | Invalid index | Verify slide exists |

## Resources
- [Gamma Export API](https://gamma.app/docs/export)
- [Gamma Asset Management](https://gamma.app/docs/assets)

## Next Steps
Proceed to `gamma-common-errors` for error handling patterns.

## Examples

**Basic usage**: Apply gamma core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma core workflow b for production environments with multiple constraints and team-specific requirements.