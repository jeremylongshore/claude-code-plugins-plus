---
name: obsidian-core-workflow-a
description: |
  Execute Obsidian primary workflow: note manipulation and vault operations.
  Use when implementing file operations, frontmatter handling,
  or programmatic note creation and modification.
  Trigger with phrases like "obsidian vault operations",
  "obsidian file manipulation", "obsidian note management".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Core Workflow A: Vault Operations

## Overview
Primary workflow for Obsidian plugin development: manipulating notes, handling frontmatter, and working with the vault file system.

## Prerequisites
- Completed `obsidian-install-auth` setup
- Understanding of Obsidian's file structure
- Valid development vault configured

## Instructions

### Step 1: Working with Files (TFile)

### Step 2: Frontmatter Operations

### Step 3: Link and Tag Operations

### Step 4: Search and Query

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- File operations for create, read, update, delete
- Frontmatter parsing and modification
- Link and tag traversal
- Search and query capabilities

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| File not found | Path incorrect | Verify with `getAbstractFileByPath` |
| Permission denied | File locked | Check if file is open in editor |
| YAML parse error | Invalid frontmatter | Validate YAML syntax |
| Circular links | Recursive backlinks | Track visited files |

## Resources
- [Obsidian Developer Docs - Vault](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [Obsidian MetadataCache](https://docs.obsidian.md/Reference/TypeScript+API/MetadataCache)

## Next Steps
For UI components, see `obsidian-core-workflow-b`.

## Examples

**Basic usage**: Apply obsidian core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian core workflow a for production environments with multiple constraints and team-specific requirements.