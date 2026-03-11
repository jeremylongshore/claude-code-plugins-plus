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
Comprehensive search and retrieval workflow for Evernote, including search grammar, filters, pagination, and related notes discovery.

## Prerequisites
- Completed `evernote-install-auth` setup
- Understanding of Evernote search grammar
- Valid access token configured

## Instructions

### Step 1: Search Service Foundation

### Step 2: Advanced Search Grammar Builder

### Step 3: Paginated Search Results

### Step 4: Related Notes Discovery

### Step 5: Search Result Enrichment

### Step 6: Complete Search Workflow Example

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Flexible search service with query builder
- Search grammar support for complex queries
- Paginated results for large datasets
- Related notes discovery
- Enriched results with notebook/tag names

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RATE_LIMIT_REACHED` | Too many searches | Add delay between requests |
| `INVALID_SEARCH` | Bad search grammar | Validate query syntax |
| `QUOTA_REACHED` | Search quota exceeded | Reduce search frequency |

## Resources
- [Search Grammar](https://dev.evernote.com/doc/articles/search_grammar.php)
- [Search Overview](https://dev.evernote.com/doc/articles/search.php)
- [Related Notes](https://dev.evernote.com/doc/articles/related_notes.php)

## Next Steps
For error handling patterns, see `evernote-common-errors`.

## Examples

**Basic usage**: Apply evernote core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote core workflow b for production environments with multiple constraints and team-specific requirements.