---
name: evernote-core-workflow-a
description: |
  Execute Evernote primary workflow: Note Creation and Management.
  Use when creating notes, organizing content, managing notebooks,
  or implementing note-taking features.
  Trigger with phrases like "create evernote note", "evernote note workflow",
  "manage evernote notes", "evernote content".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Evernote Core Workflow A: Note Creation & Management

## Overview
Primary workflow for creating, organizing, and managing notes in Evernote. This covers the essential CRUD operations that form the foundation of any Evernote integration.

## Prerequisites
- Completed `evernote-install-auth` setup
- Understanding of ENML format
- Valid access token configured

## Instructions

### Step 1: Note Creation Service

### Step 2: Note Retrieval and Reading

### Step 3: Note Updates

### Step 4: Note Organization

### Step 5: Complete Workflow Example

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Fully functional note creation service
- ENML content formatting
- Notebook organization
- Tag management
- Todo list support
- Content append/update operations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `BAD_DATA_FORMAT` | Invalid ENML | Use wrapInENML helper, validate content |
| `LIMIT_REACHED` | Too many notebooks (250 max) | Clean up unused notebooks |
| `DATA_REQUIRED` | Missing title or content | Validate inputs before API call |
| `INVALID_USER` | Token expired | Re-authenticate user |

## Resources
- [Creating Notes](https://dev.evernote.com/doc/articles/creating_notes.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Note Types Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For search and retrieval workflows, see `evernote-core-workflow-b`.
