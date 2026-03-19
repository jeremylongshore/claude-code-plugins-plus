---
name: gamma-migration-deep-dive
description: |
  Deep dive into migrating to Gamma from other presentation platforms.
  Use when migrating from PowerPoint, Google Slides, Canva,
  or other presentation tools to Gamma.
  Trigger with phrases like "gamma migration", "migrate to gamma",
  "gamma import", "gamma from powerpoint", "gamma from google slides".
allowed-tools: Read, Write, Edit, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Migration Deep Dive

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
Comprehensive guide for migrating presentations and workflows from PowerPoint, Google Slides, Canva, and other platforms to Gamma with validation and rollback support.

## Prerequisites
- Gamma API access
- Source platform export capabilities
- Node.js 18+ for migration scripts
- Sufficient Gamma storage quota

## Instructions

### Step 1: Inventory Source Presentations
Scan source directories for `.pptx`, `.pdf`, and `.key` files. Generate a JSON inventory with metadata (title, size, source platform, last modified).

### Step 2: Build Migration Engine
Create a migration engine with concurrent batch processing, retry logic, and progress reporting. Use `PQueue` for concurrency control.

### Step 3: Handle Platform-Specific Exports
- **Google Slides**: Export via Drive API as `.pptx`, then import to Gamma
- **PowerPoint**: Extract metadata from `docProps/core.xml` before import
- **Canva/Keynote**: Export as `.pptx` first, then import

### Step 4: Validate Migrated Presentations
Verify each migrated presentation has slides, all assets loaded, and can export.

### Step 5: Create Rollback Snapshots
Save source-to-Gamma ID mappings as snapshots. If migration fails, delete Gamma copies.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Migration inventory JSON
- Batch migration with concurrency control
- Platform-specific import handlers
- Validation and rollback support

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import timeout | Large file size | Increase timeout to 120s |
| Asset missing | Embedded fonts/media | Re-export with embedded assets |
| Format mismatch | Unsupported features | Export as PDF fallback |

## Examples

### Supported Migration Paths
| Source | Format | Fidelity | Notes |
|--------|--------|----------|-------|
| PowerPoint | .pptx | High | Native import |
| Google Slides | .pptx export | High | Export first |
| Canva | .pdf/.pptx | Medium | Limited animations |
| Keynote | .pptx export | High | Export first |
| Markdown | .md | High | Structure preserved |

### Migration Checklist
- [ ] Inventory all source presentations
- [ ] Test import with sample files
- [ ] Run migration in batches
- [ ] Validate each batch
- [ ] Update links and references

## Resources
- [Gamma Import Formats](https://gamma.app/docs/import)
- [Migration Best Practices](https://gamma.app/docs/migration)