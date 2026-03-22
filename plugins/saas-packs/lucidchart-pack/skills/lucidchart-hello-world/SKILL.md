---
name: lucidchart-hello-world
description: |
  Create a minimal working Lucidchart example.
  Trigger: "lucidchart hello world", "lucidchart example", "test lucidchart".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Hello World

## Overview
Minimal working examples demonstrating core Lucidchart API functionality.

## Instructions

### Step 1: Create a Document
```typescript
const doc = await client.documents.create({
  title: 'API Architecture Diagram',
  product: 'lucidchart'  // or 'lucidspark'
});
console.log(`Document: ${doc.documentId}`);
console.log(`Edit URL: ${doc.editUrl}`);
```

### Step 2: Add Shapes via Standard Import
```typescript
// Lucid Standard Import uses .lucid file format
const importData = {
  pages: [{
    id: 'page1',
    title: 'Main',
    shapes: [
      { id: 's1', type: 'rectangle', boundingBox: { x: 100, y: 100, w: 200, h: 80 },
        text: 'API Gateway', style: { fill: '#4A90D9' } },
      { id: 's2', type: 'rectangle', boundingBox: { x: 100, y: 300, w: 200, h: 80 },
        text: 'Database', style: { fill: '#7B68EE' } }
    ],
    lines: [
      { id: 'l1', endpoint1: { shapeId: 's1' }, endpoint2: { shapeId: 's2' },
        stroke: { color: '#333', width: 2 } }
    ]
  }]
};
await client.documents.import(doc.documentId, importData);
```

### Step 3: Export Document
```typescript
const png = await client.documents.export(doc.documentId, {
  format: 'png', pageIndex: 0, scale: 2
});
fs.writeFileSync('diagram.png', png);
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Auth error | Invalid credentials | Check LUCID_API_KEY |
| Not found | Invalid endpoint | Verify API URL |
| Rate limit | Too many requests | Implement backoff |

## Resources
- [Lucidchart API Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-local-dev-loop`.
