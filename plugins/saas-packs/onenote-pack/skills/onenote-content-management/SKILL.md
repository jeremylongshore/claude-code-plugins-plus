---
name: onenote-content-management
description: |
  Execute OneNote primary workflow: Page & Content Management.
  Use when creating pages from templates or external data,
  updating task databases from CI/CD pipeline events, or archiving and organizing content by project or date.
  Trigger with phrases like "onenote manage pages",
  "create or update pages with onenote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote Page & Content Management

## Overview
Create, read, update, and organize pages, databases, and content blocks.
This is the primary workflow — programmatic content management.


## Prerequisites
- Completed `onenote-install-auth` setup

- Understanding of OneNote core concepts

- Valid API credentials configured

## Instructions

### Step 1: Create Page with Content
```typescript
const page = await client.pages.create({
  parentId: workspace.rootPageId,
  title: 'Sprint 42 Retrospective',
  content: [
    { type: 'heading_2', text: 'What went well' },
    { type: 'bulleted_list', items: ['Shipped feature X on time', 'Zero P0 incidents'] },
    { type: 'heading_2', text: 'What to improve' },
    { type: 'bulleted_list', items: ['Better test coverage', 'Earlier design reviews'] },
  ],
});
console.log(`Created: ${page.url}`);

```

### Step 2: Query Database Records
```typescript
const tasks = await client.databases.query(taskDbId, {
  filter: {
    and: [
      { property: 'Status', status: { equals: 'In Progress' } },
      { property: 'Assignee', people: { contains: userId } },
    ],
  },
  sorts: [{ property: 'Priority', direction: 'descending' }],
});
console.log(`${tasks.results.length} tasks in progress`);

```

### Step 3: Update Records
```typescript
for (const task of completedTasks) {
  await client.pages.update(task.id, {
    properties: {
      Status: { status: { name: 'Done' } },
      'Completed Date': { date: { start: new Date().toISOString() } },
    },
  });
}
console.log(`Marked ${completedTasks.length} tasks as Done`);

```

## Output
- Completed Page & Content Management execution

- Expected results from OneNote API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Page Not Found | Page ID is invalid or page was deleted/archived | Search by title instead of ID. Check trash/archive for deleted pages. |
| Validation Error | Page content or property value doesn't match database schema | Check database schema for required properties and allowed values. |

## Examples

### Complete Workflow
```typescript
const client = new ProductivityClient({ apiKey: process.env.API_KEY });

async function createFromTemplate(templateId: string, title: string, data: Record<string, any>) {
  const template = await client.pages.get(templateId);
  const page = await client.pages.create({
    parentId: template.parentId,
    title,
    content: applyData(template.content, data),
  });
  return page;
}

```

### Common Variations
- **Database sync**: Mirror external data (GitHub issues, Jira tickets) into a database
- **Template instantiation**: Create pages from templates with variable substitution
- **Bulk archive**: Archive completed items older than N days


## Resources
- [OneNote Documentation](https://docs.onenote.com)
- [OneNote API Reference](https://docs.onenote.com/api)

## Next Steps
For secondary workflow, see `onenote-search-retrieve`.