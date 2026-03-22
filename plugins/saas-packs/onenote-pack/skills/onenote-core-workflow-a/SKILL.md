---
name: onenote-core-workflow-a
description: |
  Execute OneNote primary workflow: Notebook & Page Management.
  Trigger: "onenote notebook & page management", "primary onenote workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote — Notebook & Page Management

## Overview
Primary workflow for OneNote integration.

## Instructions

### Step 1: Create a Notebook
```typescript
const notebook = await client.api('/me/onenote/notebooks').post({
  displayName: 'Project Notes'
});
console.log(`Notebook: ${notebook.id}`);
```

### Step 2: Create a Section
```typescript
const section = await client.api(`/me/onenote/notebooks/${notebook.id}/sections`).post({
  displayName: 'Sprint 1'
});
```

### Step 3: Create a Page with HTML Content
```typescript
// Pages use HTML for content
const htmlContent = `
  <!DOCTYPE html>
  <html>
  <head><title>Meeting Notes</title></head>
  <body>
    <h1>Sprint Planning — March 22, 2026</h1>
    <p>Attendees: Alice, Bob, Charlie</p>
    <h2>Action Items</h2>
    <ul>
      <li data-tag="to-do">Deploy feature X by Friday</li>
      <li data-tag="to-do">Review PR #123</li>
    </ul>
    <img src="name:diagram" alt="Architecture" />
  </body>
  </html>
`;

const page = await client.api(`/me/onenote/sections/${section.id}/pages`)
  .header('Content-Type', 'text/html')
  .post(htmlContent);
console.log(`Page: ${page.id} — ${page.title}`);
```

### Step 4: Get Page Content
```typescript
const content = await client.api(`/me/onenote/pages/${page.id}/content`).get();
// Returns HTML content of the page
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-core-workflow-b`.
