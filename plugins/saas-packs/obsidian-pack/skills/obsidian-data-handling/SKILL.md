---
name: obsidian-data-handling
description: |
  Implement vault data backup, sync, and recovery strategies.
  Use when building backup features, implementing data export,
  or handling vault synchronization in your plugin.
  Trigger with phrases like "obsidian backup", "obsidian sync",
  "obsidian data export", "vault backup strategy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Data Handling

## Overview
Implement robust data handling patterns for vault backup, export, sync, and recovery in Obsidian plugins.

## Prerequisites
- Understanding of Obsidian file system
- Knowledge of data serialization formats
- Basic understanding of sync patterns

## Instructions

### Step 1: Data Export Service

### Step 2: Data Import Service

### Step 3: Backup Service

### Step 4: Data Validation

### Step 5: Data Sync Patterns

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Data export with multiple formats
- Import with conflict handling
- Automated backup with retention
- Vault validation
- Change tracking for sync

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Export fails | Large vault | Use streaming export |
| Import conflicts | Existing files | Provide overwrite option |
| Backup corruption | Interrupted write | Verify with checksum |
| Sync conflicts | Concurrent edits | Implement conflict resolution |

## Resources
- [Obsidian Sync](https://help.obsidian.md/Obsidian+Sync)
- [Git for Obsidian](https://github.com/denolehov/obsidian-git)

## Next Steps
For team access patterns, see `obsidian-enterprise-rbac`.
