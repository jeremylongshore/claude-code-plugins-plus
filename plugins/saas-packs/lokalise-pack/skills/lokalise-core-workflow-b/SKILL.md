---
name: lokalise-core-workflow-b
description: |
  Execute Lokalise secondary workflow: Download translations and integrate with app.
  Use when downloading translation files, exporting translations,
  or integrating Lokalise output into your application.
  Trigger with phrases like "lokalise download", "lokalise pull translations",
  "export lokalise", "get translations from lokalise".
allowed-tools: Read, Write, Edit, Bash(lokalise2:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Core Workflow B

## Overview
Secondary workflow for downloading translations from Lokalise and integrating them into your application.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Lokalise project with translations
- Target directory for downloaded files

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Downloaded translation files in target format
- Extracted to project locales directory
- Optional TypeScript types generated
- Integration with i18n library

## Error Handling
| Aspect | Workflow A (Upload) | Workflow B (Download) |
|--------|---------------------|----------------------|
| Direction | Source -> Lokalise | Lokalise -> App |
| Trigger | Dev adds strings | Build/deploy |
| Format | Any supported | Target format |
| Frequency | On change | On build |

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Project not found` | Wrong project ID | Verify project_id |
| `Empty bundle` | No translations | Check filter options |
| `Invalid format` | Unsupported export | Check format parameter |
| `Download timeout` | Large project | Increase timeout |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [File Download API](https://developers.lokalise.com/reference/download-files)
- [Export Options](https://docs.lokalise.com/en/articles/1400465-exporting-translation-files)
- [Bundle Structure Placeholders](https://docs.lokalise.com/en/articles/2281317-filenames)

## Next Steps
For common errors, see `lokalise-common-errors`.