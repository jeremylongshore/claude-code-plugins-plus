---
name: lokalise-migration-deep-dive
description: |
  Execute major migration to Lokalise from other TMS platforms with data migration strategies.
  Use when migrating to Lokalise from competitors, performing data imports,
  or re-platforming existing translation management to Lokalise.
  Trigger with phrases like "migrate to lokalise", "lokalise migration",
  "switch to lokalise", "lokalise import", "lokalise replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(lokalise2:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Migration Deep Dive

## Overview
Comprehensive guide for migrating to Lokalise from other TMS platforms or legacy systems.

## Prerequisites
- Access to source system for export
- Lokalise account with appropriate plan
- Understanding of current translation workflow
- Rollback strategy defined

## Instructions
1. **Migration Types**
2. **Instructions**
3. **Flagship+ Skills**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Migration assessment complete
- Data exported and transformed
- Lokalise project created
- Keys and translations imported
- Migration validated

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Key name conflicts | Different naming conventions | Normalize keys before import |
| Missing translations | Export incomplete | Re-export from source |
| Encoding issues | Non-UTF8 files | Convert to UTF-8 |
| Rate limit during import | Too fast | Increase delays between batches |
| Placeholder mismatch | Different syntax | Transform placeholders |

## Examples
### Migration Rollback
```bash
#!/bin/bash
# rollback-migration.sh

# If migration fails, delete the new project
lokalise2 --token "$LOKALISE_API_TOKEN" \
  project delete --project-id "$NEW_PROJECT_ID"

# Keep using old system
echo "Migration rolled back. Continue using source system."
```

## Resources
- [Lokalise Import Guide](https://docs.lokalise.com/en/articles/1400492-uploading-translation-files)
- [Supported File Formats](https://docs.lokalise.com/en/articles/1400452-file-formats)
- [Migration Case Studies](https://lokalise.com/case-studies)
