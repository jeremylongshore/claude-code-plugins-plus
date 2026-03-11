---
name: evernote-hello-world
description: |
  Create a minimal working Evernote example.
  Use when starting a new Evernote integration, testing your setup,
  or learning basic Evernote API patterns.
  Trigger with phrases like "evernote hello world", "evernote example",
  "evernote quick start", "simple evernote code", "create first note".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Hello World

## Overview
Create your first Evernote note using the Cloud API, demonstrating ENML format and NoteStore operations.

## Prerequisites
- Completed `evernote-install-auth` setup
- Valid access token (OAuth or Developer Token for sandbox)
- Development environment ready

## Instructions

### Step 1: Create Entry File

### Step 2: Understand ENML Format

### Step 3: Create Your First Note

### Step 4: Python Version

### Step 5: List Notebooks

### Step 6: Retrieve a Note

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Working code file with Evernote client initialization
- Successfully created note in your Evernote account
- Console output with note GUID and confirmation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `EDAMUserException: BAD_DATA_FORMAT` | Invalid ENML content | Validate against ENML DTD |
| `EDAMNotFoundException` | Note or notebook not found | Check GUID is correct |
| `EDAMSystemException: RATE_LIMIT_REACHED` | Too many requests | Wait for `rateLimitDuration` |
| `Missing DOCTYPE` | ENML missing required header | Add XML declaration and DOCTYPE |

## Resources
- [Creating Notes](https://dev.evernote.com/doc/articles/creating_notes.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Core Concepts](https://dev.evernote.com/doc/articles/core_concepts.php)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
Proceed to `evernote-local-dev-loop` for development workflow setup.

## Examples

**Basic usage**: Apply evernote hello world to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote hello world for production environments with multiple constraints and team-specific requirements.