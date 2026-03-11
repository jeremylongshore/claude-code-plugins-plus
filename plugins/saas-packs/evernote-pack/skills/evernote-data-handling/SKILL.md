---
name: evernote-data-handling
description: |
  Best practices for handling Evernote data.
  Use when implementing data storage, processing notes,
  handling attachments, or ensuring data integrity.
  Trigger with phrases like "evernote data", "handle evernote notes",
  "evernote storage", "process evernote content".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Data Handling

## Overview
Best practices for handling Evernote data including notes, attachments, ENML content, and synchronization data.

## Prerequisites
- Understanding of Evernote data model
- Database for local storage
- File storage for attachments

## Instructions

### Step 1: Data Schema Design

### Step 2: ENML Content Processing

### Step 3: Resource (Attachment) Handling

### Step 4: Sync Data Manager

### Step 5: Data Export

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Database schema for Evernote data
- ENML content processor
- Resource/attachment handler
- Sync data manager
- Data export utility

## Resources
- [Evernote Data Model](https://dev.evernote.com/doc/articles/data_model.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)

## Next Steps
For enterprise features, see `evernote-enterprise-rbac`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with content |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote data handling for production environments with multiple constraints and team-specific requirements.