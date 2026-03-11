---
name: obsidian-local-dev-loop
description: |
  Configure Obsidian plugin development with hot-reload and fast iteration.
  Use when setting up development workflow, configuring test vaults,
  or establishing a rapid development cycle.
  Trigger with phrases like "obsidian dev loop", "obsidian hot reload",
  "obsidian development workflow", "develop obsidian plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Obsidian plugins with hot-reload and testing.

## Prerequisites
- Completed `obsidian-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Obsidian desktop app

## Instructions

### Step 1: Configure Development Vault

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Dedicated development vault with test data
- Symlinked plugin for instant updates
- Hot-reload via BRAT or file watching
- Watch mode build with source maps
- Fast iteration cycle

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not reloading | BRAT not configured | Install and enable BRAT plugin |
| Symlink not working | Permission denied | Run as admin (Windows) |
| Build not triggering | Watch mode not started | Run `npm run dev` |
| Source maps not working | Disabled in config | Set `sourcemap: "inline"` |
| TypeScript errors | Missing types | Run `npm install` |

## Resources
- [BRAT Plugin](https://github.com/TfTHacker/obsidian42-brat)
- [esbuild Documentation](https://esbuild.github.io/)
- [Obsidian Plugin Development Docs](https://docs.obsidian.md/Plugins/Getting+started/Development+workflow)

## Next Steps
See `obsidian-sdk-patterns` for production-ready code patterns.
