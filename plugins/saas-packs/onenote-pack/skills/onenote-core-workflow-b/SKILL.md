---
name: onenote-core-workflow-b
description: |
  Execute OneNote secondary workflow: Search & Content Extraction.
  Trigger: "onenote search & content extraction", "secondary onenote workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote — Search & Content Extraction

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: List All Pages
```typescript
const pages = await client.api('/me/onenote/pages')
  .top(20)
  .orderby('lastModifiedDateTime desc')
  .get();
pages.value.forEach(p =>
  console.log(`${p.title} — Modified: ${p.lastModifiedDateTime}`)
);
```

### Step 2: Get Pages from Specific Notebook
```typescript
const notebookPages = await client.api(
  `/me/onenote/notebooks/${notebookId}/pages`
).expand('parentSection').get();

notebookPages.value.forEach(p =>
  console.log(`[${p.parentSection.displayName}] ${p.title}`)
);
```

### Step 3: Search Pages by Content
```typescript
// OData filter for pages
const results = await client.api('/me/onenote/pages')
  .filter("contains(title, 'meeting')")
  .top(10)
  .get();
```

### Step 4: Update Page Content
```typescript
// PATCH with specific target (append, replace, etc.)
await client.api(`/me/onenote/pages/${pageId}/content`).patch([
  {
    target: 'body',
    action: 'append',
    content: '<p>Updated: New action item added</p>'
  }
]);
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-common-errors`.
