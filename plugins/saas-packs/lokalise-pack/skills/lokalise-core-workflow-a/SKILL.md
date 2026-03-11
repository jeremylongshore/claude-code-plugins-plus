---
name: lokalise-core-workflow-a
description: |
  Execute Lokalise primary workflow: Upload source files and manage translation keys.
  Use when uploading translation files, creating/updating keys,
  or managing source strings in Lokalise projects.
  Trigger with phrases like "lokalise upload", "lokalise push keys",
  "lokalise source strings", "add translations to lokalise".
allowed-tools: Read, Write, Edit, Bash(lokalise2:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Core Workflow A

## Overview
Primary workflow for uploading source translation files and managing keys in Lokalise.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Lokalise project created
- Source translation file (JSON, XLIFF, PO, etc.)

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Source file uploaded to Lokalise
- Keys created with translations
- Keys tagged for organization
- Bulk operations completed

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `400 Invalid file format` | Unsupported format | Check supported formats |
| `400 Key already exists` | Duplicate key name | Use replace_modified or unique names |
| `413 Payload too large` | File too big | Split into smaller files |
| `429 Rate limited` | Too many requests | Use --poll flag, wait between uploads |

## Examples
### Upload with Cleanup Options
```bash
lokalise2 file upload \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --file "./locales/en.json" \
  --lang-iso en \
  --cleanup-mode                  # Remove keys not in file
  --replace-modified              # Update existing translations
  --fill-empty                    # Copy base to empty translations
  --poll
```

## Resources
- [File Upload API](https://developers.lokalise.com/reference/upload-a-file)
- [Keys API](https://developers.lokalise.com/reference/create-keys)
- [Supported Formats](https://docs.lokalise.com/en/articles/1400492-uploading-translation-files)

## Next Steps
For downloading translations, see `lokalise-core-workflow-b`.