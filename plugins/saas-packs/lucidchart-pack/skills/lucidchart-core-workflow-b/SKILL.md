---
name: lucidchart-core-workflow-b
description: |
  Execute Lucidchart secondary workflow: Data-Linked Diagrams.
  Trigger: "lucidchart data-linked diagrams", "secondary lucidchart workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart — Data-Linked Diagrams

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Import CSV Data
```typescript
// Create data-linked diagram from CSV
const data = [
  { name: 'Service A', status: 'healthy', latency: '45ms' },
  { name: 'Service B', status: 'degraded', latency: '200ms' },
  { name: 'Service C', status: 'healthy', latency: '30ms' }
];

await client.dataSources.import(doc.documentId, {
  format: 'json',
  data: data,
  mapping: {
    shapeText: 'name',
    shapeColor: { field: 'status', values: { healthy: '#4CAF50', degraded: '#FF9800' } }
  }
});
```

### Step 2: Share and Collaborate
```typescript
await client.documents.share(doc.documentId, {
  email: 'team@example.com',
  role: 'editor',  // viewer, commenter, editor
  message: 'Please review this architecture diagram'
});
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-common-errors`.
