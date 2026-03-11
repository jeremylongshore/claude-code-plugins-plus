---
name: obsidian-migration-deep-dive
description: |
  Execute major Obsidian plugin rewrites and migration strategies.
  Use when migrating to or from Obsidian, performing major plugin rewrites,
  or re-platforming existing note systems to Obsidian.
  Trigger with phrases like "migrate to obsidian", "obsidian migration",
  "convert notes to obsidian", "obsidian replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Migration Deep Dive

## Overview
Comprehensive guide for migrating to Obsidian from other note-taking apps, or performing major plugin architecture rewrites.

## Prerequisites
- Source data access
- Understanding of Obsidian vault structure
- Node.js for scripted migrations
- Backup of source data

## Instructions

### Step 1: Pre-Migration Assessment

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Pre-migration assessment
- Format converters for common apps
- Link migration and fixing
- Batch migration scripts
- Migration reports

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Encoding errors | Non-UTF8 content | Detect and convert encoding |
| Broken links | Renamed/deleted files | Generate orphaned links report |
| Missing attachments | Export incomplete | Re-export with attachments |
| Duplicate files | Same name different folders | Add path prefix |

## Resources
- [Obsidian Import/Export](https://help.obsidian.md/import)
- [Evernote Export Format](https://evernote.com/blog/how-evernotes-xml-export-format-works)
- [Notion Export](https://www.notion.so/help/export-your-content)

## Next Steps
1. Review migrated content
2. Check orphaned links report

## Examples

**Basic usage**: Apply obsidian migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian migration deep dive for production environments with multiple constraints and team-specific requirements.