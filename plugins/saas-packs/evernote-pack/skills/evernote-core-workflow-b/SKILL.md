---
name: evernote-core-workflow-b
description: |
  Execute Evernote secondary workflow: Search and Retrieval.
  Use when implementing search features, finding notes,
  filtering content, or building search interfaces.
  Trigger with phrases like "search evernote", "find evernote notes",
  "evernote search", "query evernote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Core Workflow B: Search & Retrieval

## Overview
Comprehensive search and retrieval workflow for Evernote, including search grammar, filters, pagination, related notes discovery, and result enrichment with notebook/tag names.

## Prerequisites
- Completed `evernote-install-auth` setup
- Understanding of Evernote search grammar
- Valid access token configured

## Instructions

### Step 1: Search Service Foundation

Build a `SearchService` wrapping `findNotesMetadata()`. Use `NoteFilter` for query terms, sort order, and notebook scope. Use `NotesMetadataResultSpec` to control which metadata fields are returned (title, dates, tags, notebook GUID).

```javascript
const filter = new Evernote.NoteStore.NoteFilter({
  words: 'tag:urgent notebook:"Work"',
  ascending: false,
  order: Evernote.Types.NoteSortOrder.UPDATED
});

const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
  includeTitle: true, includeUpdated: true,
  includeTagGuids: true, includeNotebookGuid: true
});

const result = await noteStore.findNotesMetadata(filter, 0, 50, spec);
```

### Step 2: Advanced Search Grammar Builder

Implement a fluent `QueryBuilder` class that chains operators: `notebook("Work")`, `tag("urgent")`, `intitle("meeting")`, `createdAfter(date)`, `hasUncompletedTodos()`, `hasAttachments()`. Call `.build()` to produce the query string. Use `any:` prefix for OR logic.

```javascript
const query = new QueryBuilder()
  .notebook('Work')
  .tag('urgent')
  .lastNDays(7)
  .hasUncompletedTodos()
  .build();
// Result: 'notebook:"Work" tag:"urgent" created:day-7 todo:false'
```

### Step 3: Paginated Search Results

Use an async generator to iterate through large result sets page by page. Track `offset` and compare against `totalNotes` to determine when to stop. Default page size of 50-100 balances API calls versus response size.

### Step 4: Related Notes Discovery

Call `noteStore.findRelated()` with a `RelatedQuery` (by note GUID or plain text) and `RelatedResultSpec` to discover related notes, notebooks, and tags.

### Step 5: Search Result Enrichment

Cache notebook and tag lookups, then map GUIDs to human-readable names. Return enriched results with `notebookName`, `tags[]`, `created`, and `updated` fields.

For the full `SearchService`, `QueryBuilder`, pagination, and enrichment implementations, see [Implementation Guide](references/implementation-guide.md).

## Search Grammar Quick Reference

| Operator | Example | Description |
|----------|---------|-------------|
| `notebook:` | `notebook:"Work"` | Restrict to notebook |
| `tag:` | `tag:urgent` | Has tag |
| `-tag:` | `-tag:archived` | Exclude tag |
| `intitle:` | `intitle:meeting` | Word in title |
| `created:` | `created:day-7` | Created within last 7 days |
| `updated:` | `updated:week` | Updated this week |
| `todo:` | `todo:false` | Has uncompleted todos |
| `resource:` | `resource:image/*` | Has attachment type |
| `any:` | `any: term1 term2` | Match ANY term (default is AND) |

## Output
- `SearchService` with text search, notebook search, and tag search
- Fluent `QueryBuilder` for composing search grammar queries
- Async generator for paginated results
- Related notes discovery via `findRelated()`
- Enriched results with notebook and tag names

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RATE_LIMIT_REACHED` | Too many search calls | Add delay between paginated requests |
| `BAD_DATA_FORMAT` | Invalid search grammar syntax | Validate query with `QueryBuilder` |
| `QUOTA_REACHED` | Search quota exceeded | Reduce search frequency, cache results |

## Resources
- [Search Grammar](https://dev.evernote.com/doc/articles/search_grammar.php)
- [Search Overview](https://dev.evernote.com/doc/articles/search.php)
- [Related Notes](https://dev.evernote.com/doc/articles/related_notes.php)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For error handling patterns, see `evernote-common-errors`.

## Examples

**Find action items**: Search for notes with uncompleted todos from the past week using `QueryBuilder().thisWeek().hasUncompletedTodos().build()`. Enrich results with notebook names.

**Meeting search**: Find all notes titled "meeting" in the "Work" notebook from the last 30 days, paginate through results, and export titles with tags.
