---
name: granola-migration-deep-dive
description: |
  Deep dive migration guide from other meeting note tools to Granola.
  Use when migrating from Otter.ai, Fireflies, Fathom, or other tools,
  planning data migration, or executing transition strategies.
  Trigger with phrases like "migrate to granola", "switch to granola",
  "granola from otter", "granola from fireflies", "granola migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide for migrating to Granola from Otter.ai, Fireflies, Fathom, Zoom, Google Meet, or Microsoft Teams.

## Prerequisites
- Access to source tool with export capability
- Granola workspace configured
- Migration timeline agreed with stakeholders

## Migration Sources

| Tool | Export Format | Complexity |
|------|-------------|------------|
| Otter.ai | TXT, SRT, PDF | Medium |
| Fireflies.ai | TXT, JSON, PDF | Medium |
| Fathom | Markdown, CSV | Low |
| Zoom/Meet/Teams | VTT, TXT | Low |

## Instructions

### Step 1: Choose Migration Strategy
- **Clean Start** (<100 meetings): Start fresh, archive history externally
- **Selective** (100-1000): Migrate key meetings only (client calls, decisions)
- **Full** (Enterprise): Export everything, transform, import all

### Step 2: Assess and Inventory
Document total meetings, date range, storage size, content types, and integration dependencies.

### Step 3: Export from Source
Follow source-specific export procedures (bulk export for Pro/Enterprise plans).

### Step 4: Convert and Import
Run conversion scripts to transform source formats to Granola-compatible Markdown. Archive in Notion/Drive.

### Step 5: Parallel Run (2 weeks)
Record in Granola as primary while keeping source as backup. Compare quality daily.

### Step 6: Cutover
Final export from source, disable source recording, cancel subscription, monitor closely for 3 days.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for source-specific export procedures, conversion scripts, execution timeline, communication templates, and rollback plan.

## Output
- Source data exported and backed up
- Historical meetings converted and archived
- Granola configured with integrations
- Team migrated and recording in Granola

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing transcripts | Export format limitation | Re-export in different format |
| Failed conversion | Unexpected source format | Update conversion script |
| Low adoption | Insufficient training | Add training sessions, share quick wins |
| Data gaps | Incomplete export | Run secondary export, verify counts |

## Examples

### Quick Migration Assessment
```markdown
- Total meetings to migrate: ___
- Date range: ___ to ___
- Strategy: Clean Start / Selective / Full
- Target cutover date: ___
- Parallel running: ___ weeks
```

## Resources
- [Granola Migration Guide](https://granola.ai/help/migration)
- [Import Support](https://granola.ai/support)
- [Enterprise Migration Services](https://granola.ai/enterprise)

## Next Steps
Proceed to `granola-performance-tuning` for optimization.