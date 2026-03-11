---
name: obsidian-common-errors
description: |
  Diagnose and fix common Obsidian plugin errors and exceptions.
  Use when encountering plugin errors, debugging failed operations,
  or troubleshooting Obsidian plugin issues.
  Trigger with phrases like "obsidian error", "fix obsidian plugin",
  "obsidian not working", "debug obsidian plugin".
allowed-tools: Read, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Common Errors

## Overview
Quick reference for the most common Obsidian plugin errors and their solutions.

## Prerequisites
- Obsidian plugin development environment set up
- Access to Developer Console (Ctrl/Cmd+Shift+I)
- Plugin source code access

## Instructions

### Step 1: Open Developer Console

### Step 2: Identify the Error

### Step 3: Match Error to Solutions Below

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Error Handling
### TypeError: Cannot read properties of undefined

**Error Message:**
```
TypeError: Cannot read properties of undefined (reading 'xyz')
```

**Cause:** Accessing a property on a null/undefined object, often when vault or workspace isn't ready.

## Resources
- [Obsidian Developer Docs](https://docs.obsidian.md/Plugins)
- [Obsidian Forum - Developers](https://forum.obsidian.md/c/developers/14)
- [Obsidian Discord](https://discord.gg/obsidianmd)

## Next Steps
For comprehensive debugging, see `obsidian-debug-bundle`.
