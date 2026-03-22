---
name: notion-search-retrieve
description: |
  Execute Notion secondary workflow: Search & Knowledge Retrieval.
  Use when finding relevant pages by keyword or tag,
  or building a knowledge base search for internal tools.
  Trigger with phrases like "notion search",
  "search content with notion".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion Search & Knowledge Retrieval

## Overview
Search across all content and retrieve specific pages, blocks, or database entries.
The read workflow for building knowledge-aware applications.


## Prerequisites
- Completed `notion-install-auth` setup
- Familiarity with `notion-content-management`
- Valid API credentials configured

## Instructions

### Step 1: Full-Text Search
```typescript
const results = await client.search({
  query: 'deployment runbook',
  filter: { property: 'object', value: 'page' },
  sort: { direction: 'descending', timestamp: 'last_edited_time' },
});
console.log(`Found ${results.results.length} matching pages`);

```

### Step 2: Get Page Content
```typescript
const blocks = await client.blocks.children.list(pageId);
const text = blocks.results
  .filter(b => b.type === 'paragraph')
  .map(b => b.paragraph.rich_text.map(t => t.plain_text).join(''))
  .join('\n');

```

### Step 3: Extract and Use
```typescript
// Use retrieved content as context for AI, reports, or dashboards
console.log(`Retrieved ${text.length} characters from page`);
// Feed into RAG pipeline, generate summary, or display in dashboard

```

## Output
- Completed Search & Knowledge Retrieval execution

- Results from Notion API

- Success confirmation or error details

## Error Handling
| Aspect | Page & Content Management | Search & Knowledge Retrieval |
|--------|------------|------------|
| Use Case | creating pages from templates or external data | finding relevant pages by keyword or tag |
| Complexity | Medium | Low |
| Performance | Standard | Fast (indexed search) |

## Examples

### Complete Workflow
```typescript
async function findAndRead(query: string) {
  const results = await client.search({ query });
  if (results.results.length === 0) return null;
  const page = results.results[0];
  const content = await client.blocks.children.list(page.id);
  return { title: page.title, content };
}

```

### Error Recovery
```typescript
try {
  const results = await client.search({ query });
  return results;
} catch (err) {
  if (err.status === 400 && err.code === 'invalid_query') {
    // Fall back to simpler search
    return client.search({ query: query.split(' ')[0] });
  }
  throw err;
}

```

## Resources
- [Notion Documentation](https://docs.notion.com)
- [Notion API Reference](https://docs.notion.com/api)

## Next Steps
For common errors, see `notion-common-errors`.