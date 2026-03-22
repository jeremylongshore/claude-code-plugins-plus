---
name: framer-core-workflow-a
description: |
  Execute Framer primary workflow: Core Workflow A.
  Use when implementing primary use case,
  building main features, or core integration tasks.
  Trigger with phrases like "framer main workflow",
  "primary task with framer".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer, cms, plugin]
compatible-with: claude-code
---

# Framer CMS Plugin — Managed Collections

## Overview

Build a Framer plugin that syncs external data into CMS Managed Collections. Managed Collections are plugin-controlled — your plugin creates the schema and populates items. This is the primary integration pattern for connecting Framer to external CMSes, databases, or APIs.

## Prerequisites

- Completed `framer-install-auth` setup
- Plugin dev server running
- Understanding of Framer CMS concepts

## Instructions

### Step 1: Create a Managed Collection

```tsx
// src/App.tsx — CMS sync plugin
import { framer } from 'framer-plugin';
import { useState } from 'react';

framer.showUI({ width: 340, height: 400, title: 'Content Sync' });

export function App() {
  const [status, setStatus] = useState('');

  const syncCollection = async () => {
    setStatus('Fetching data...');
    const response = await fetch('https://jsonplaceholder.typicode.com/posts');
    const posts = await response.json();

    setStatus('Creating collection...');
    const collection = await framer.createManagedCollection({
      name: 'Blog Posts',
      fields: [
        { id: 'title', name: 'Title', type: 'string' },
        { id: 'body', name: 'Body', type: 'formattedText' },
        { id: 'author', name: 'Author', type: 'string' },
        { id: 'slug', name: 'Slug', type: 'slug', userEditable: false },
      ],
    });

    setStatus(`Syncing ${posts.length} items...`);
    const items = posts.slice(0, 20).map((post: any) => ({
      fieldData: {
        title: post.title,
        body: `<p>${post.body}</p>`,
        author: `User ${post.userId}`,
        slug: post.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 50),
      },
    }));

    await collection.setItems(items);
    setStatus(`Synced ${items.length} posts`);
    framer.notify(`Synced ${items.length} blog posts`);
  };

  return (
    <div style={{ padding: 16 }}>
      <h3>Blog Post Sync</h3>
      <button onClick={syncCollection} style={{ width: '100%', padding: 8 }}>Sync Now</button>
      {status && <p style={{ marginTop: 8, fontSize: 13, color: '#666' }}>{status}</p>}
    </div>
  );
}
```

### Step 2: Handle CMS Field Types

```typescript
// Framer CMS field types reference
const fields = [
  { id: 'title', name: 'Title', type: 'string' as const },
  { id: 'content', name: 'Content', type: 'formattedText' as const },
  { id: 'price', name: 'Price', type: 'number' as const },
  { id: 'featured', name: 'Featured', type: 'boolean' as const },
  { id: 'publishDate', name: 'Published', type: 'date' as const },
  { id: 'heroImage', name: 'Hero', type: 'image' as const },
  { id: 'category', name: 'Category', type: 'enum' as const, cases: [
    { id: 'tech', name: 'Technology' },
    { id: 'design', name: 'Design' },
  ]},
  { id: 'slug', name: 'Slug', type: 'slug' as const, userEditable: false },
];
```

### Step 3: Incremental Sync with Change Detection

```typescript
async function incrementalSync(collection: ManagedCollection, newData: any[]) {
  const existing = await collection.getItems();
  const existingMap = new Map(existing.map(i => [i.fieldData.slug, i]));
  const toUpsert = newData.map(item => {
    const match = existingMap.get(item.slug);
    return match ? { ...item, id: match.id } : item;
  });
  await collection.setItems(toUpsert);
}
```

### Step 4: Unmanaged Collection Access

```typescript
// Read from user-created CMS collections (not plugin-managed)
const collections = await framer.getCollections();
for (const col of collections) {
  if (col.type === 'unmanaged') {
    const items = await col.getItems();
    console.log(`${col.name}: ${items.length} items`);
  }
}
```

## Output

- Managed CMS collection with typed fields
- External data synced into Framer CMS
- Incremental sync support
- Image auto-upload from URLs

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Collection exists` | Duplicate name | Use `getManagedCollection()` first |
| `Invalid field type` | Wrong type string | Use: string, formattedText, number, boolean, date, image, enum, slug |
| `Image upload failed` | URL not public | Ensure images are publicly accessible |
| `setItems timeout` | Too many items | Batch into chunks of 100 |

## Resources

- [Framer CMS API](https://www.framer.com/developers/cms)
- [Managed Collections](https://www.framer.com/developers/reference/plugins-managed-collection)

## Next Steps

For code components and overrides, see `framer-core-workflow-b`.
