---
name: evernote-sdk-patterns
description: |
  Advanced Evernote SDK patterns and best practices.
  Use when implementing complex note operations, batch processing,
  search queries, or optimizing SDK usage.
  Trigger with phrases like "evernote sdk patterns", "evernote best practices",
  "evernote advanced", "evernote batch operations".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote SDK Patterns

## Overview
Production-ready patterns for working with the Evernote SDK, including search, filtering, batch operations, and resource handling.

## Prerequisites
- Completed `evernote-install-auth` and `evernote-hello-world`
- Understanding of Evernote data model (Notes, Notebooks, Tags, Resources)
- Familiarity with Promises/async patterns

## Instructions

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

## Output
- Reusable SDK patterns for common operations
- Efficient search with NoteFilter
- Pagination for large result sets
- Attachment handling with proper MIME types
- Tag and notebook management utilities
- Production error handling

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RATE_LIMIT_REACHED` | Too many API calls | Use rateLimitDuration, add delays |
| `BAD_DATA_FORMAT` | Invalid ENML | Validate before sending |
| `DATA_CONFLICT` | Concurrent modification | Refetch and retry |
| `QUOTA_REACHED` | Account storage full | Check user's remaining quota |

## Resources
- [API Reference](https://dev.evernote.com/doc/reference/)
- [Search Grammar](https://dev.evernote.com/doc/articles/search_grammar.php)
- [Core Concepts](https://dev.evernote.com/doc/articles/core_concepts.php)

## Next Steps
See `evernote-core-workflow-a` for note creation and management workflows.

## Examples

**Basic usage**: Apply evernote sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote sdk patterns for production environments with multiple constraints and team-specific requirements.