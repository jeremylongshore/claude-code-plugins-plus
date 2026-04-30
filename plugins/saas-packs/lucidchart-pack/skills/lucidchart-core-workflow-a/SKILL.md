---
name: lucidchart-core-workflow-a
description: 'Execute Lucidchart primary workflow: Document & Shape Creation.

  Trigger: "lucidchart document & shape creation", "primary lucidchart workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart — Document & Diagram Management

## Overview

Primary workflow for Lucidchart document and diagram management. Covers the complete
lifecycle: creating documents, adding shapes and connectors via Standard Import,
editing diagram content programmatically, and exporting to PNG, PDF, or SVG. Uses the
Lucid REST API v1 with OAuth 2.0 authorization. The Standard Import format (.lucid)
supports pages, shapes, lines, groups, and styling in a single declarative payload.

## Instructions

### Step 1: Create a Document

```typescript
const doc = await client.documents.create({
  title: 'API Architecture Diagram',
  product: 'lucidchart',  // or 'lucidspark'
});
console.log(`Document: ${doc.documentId}`);
console.log(`Edit URL: ${doc.editUrl}`);
```

### Step 2: Add Shapes and Connectors via Standard Import

```typescript
const importData = {
  pages: [{
    id: 'page1',
    title: 'Main',
    shapes: [
      { id: 's1', type: 'rectangle', boundingBox: { x: 100, y: 100, w: 200, h: 80 },
        text: 'API Gateway', style: { fill: '#4A90D9' } },
      { id: 's2', type: 'rectangle', boundingBox: { x: 100, y: 300, w: 200, h: 80 },
        text: 'Database', style: { fill: '#7B68EE' } },
      { id: 's3', type: 'rectangle', boundingBox: { x: 400, y: 200, w: 200, h: 80 },
        text: 'Auth Service', style: { fill: '#50C878' } },
    ],
    lines: [
      { id: 'l1', endpoint1: { shapeId: 's1' }, endpoint2: { shapeId: 's2' },
        stroke: { color: '#333', width: 2 } },
      { id: 'l2', endpoint1: { shapeId: 's1' }, endpoint2: { shapeId: 's3' },
        stroke: { color: '#333', width: 2, pattern: 'dashed' } },
    ],
  }],
};
await client.documents.import(doc.documentId, importData);
```

### Step 3: Edit Existing Content

```typescript
const pages = await client.documents.getPages(doc.documentId);
const pageId = pages[0].id;
// Update a shape's text and style
await client.pages.updateShape(doc.documentId, pageId, 's1', {
  text: 'API Gateway v2',
  style: { fill: '#2E86C1', fontSize: 14 },
});
```

### Step 4: Export Document

```typescript
const png = await client.documents.export(doc.documentId, {
  format: 'png',   // also: 'pdf', 'svg', 'csv' (for data shapes)
  pageIndex: 0,
  scale: 2,        // retina-quality
  crop: true,       // trim whitespace
});
fs.writeFileSync('diagram.png', png);
console.log('Exported diagram.png');
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Expired OAuth token | Refresh token or re-authorize |
| `403 Forbidden` | No edit access to document | Check sharing permissions |
| `404 Not Found` | Invalid documentId or pageId | Verify ID from create response |
| `413 Payload Too Large` | Import data exceeds 10 MB | Split into multiple pages |
| `429 Rate Limited` | Exceeds 100 req/min | Implement exponential backoff |

## Output

A successful run produces a Lucidchart document with shapes, connectors, and styling,
then exports a high-resolution PNG. Console output shows the document ID and edit URL.

## Resources

- [Lucidchart REST API](https://developer.lucid.co/reference/overview)
- [Standard Import Format](https://developer.lucid.co/docs/standard-import)
- [OAuth 2.0 Guide](https://developer.lucid.co/docs/authentication)

## Next Steps

Continue with `lucidchart-core-workflow-b` for template management and collaboration.
