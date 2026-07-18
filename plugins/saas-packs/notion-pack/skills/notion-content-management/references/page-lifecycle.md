# Page Lifecycle — Create, Update, Archive, Restore

Full walkthrough for the page lifecycle operations summarized in Step 1 of the skill.

## Create a page with typed properties and initial content

Create a page in a database with typed properties and initial block content:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Create a page with properties and inline content
async function createPage(databaseId: string) {
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    icon: { emoji: '📄' },
    cover: {
      external: { url: 'https://images.unsplash.com/photo-cover-id' },
    },
    properties: {
      // Title property (required for database pages)
      Name: {
        title: [{ text: { content: 'Q1 Sprint Retrospective' } }],
      },
      Status: {
        select: { name: 'In Progress' },
      },
      Priority: {
        select: { name: 'High' },
      },
      Tags: {
        multi_select: [{ name: 'Engineering' }, { name: 'Sprint' }],
      },
      'Due Date': {
        date: { start: '2026-04-01', end: '2026-04-05' },
      },
      Assignee: {
        people: [{ id: 'user-uuid-here' }],
      },
      Effort: {
        number: 8,
      },
      Done: {
        checkbox: false,
      },
      URL: {
        url: 'https://example.com/sprint-board',
      },
    },
    // Initial page body (block children)
    children: [
      {
        heading_2: {
          rich_text: [{ text: { content: 'Summary' } }],
        },
      },
      {
        paragraph: {
          rich_text: [{ text: { content: 'This page tracks the Q1 sprint retrospective.' } }],
        },
      },
    ],
  });

  console.log('Created page:', page.id);
  return page;
}
```

## Update page properties after creation

```typescript
async function updatePageProperties(pageId: string) {
  const updated = await notion.pages.update({
    page_id: pageId,
    properties: {
      Status: { select: { name: 'Done' } },
      Done: { checkbox: true },
      // Clear a property by setting to null
      'Due Date': { date: null },
    },
    // Update icon/cover
    icon: { emoji: '✅' },
  });

  console.log('Updated page:', updated.id);
  return updated;
}
```

## Archive and restore pages

```typescript
// Archive (soft-delete)
async function archivePage(pageId: string) {
  await notion.pages.update({ page_id: pageId, archived: true });
  console.log('Archived page:', pageId);
}

// Restore from archive
async function restorePage(pageId: string) {
  await notion.pages.update({ page_id: pageId, archived: false });
  console.log('Restored page:', pageId);
}
```
