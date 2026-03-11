---
name: obsidian-debug-bundle
description: |
  Collect Obsidian plugin debug evidence for support and troubleshooting.
  Use when encountering persistent issues, preparing bug reports,
  or collecting diagnostic information for plugin problems.
  Trigger with phrases like "obsidian debug", "obsidian diagnostic",
  "collect obsidian logs", "obsidian support bundle".
allowed-tools: Read, Bash(grep:*), Bash(tar:*), Grep, Write
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Debug Bundle

## Overview
Collect all necessary diagnostic information for Obsidian plugin bug reports and support requests.

## Prerequisites
- Obsidian plugin with issues
- Access to vault configuration
- Terminal/command line access

## Instructions

### Step 1: Create Debug Bundle Script

### Step 2: Collect System Information

### Step 3: Collect Plugin Information

### Step 4: Collect Vault Information

### Step 5: Collect Error Logs (from Console)

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- `obsidian-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - System and plugin info
  - `manifest.json` - Plugin manifest
  - `tsconfig.json` - TypeScript configuration
  - `console-log.txt` - Console output (manual)
  - `plugin-data.json` - Sanitized plugin data

## Error Handling
| Item | Purpose | Privacy |
|------|---------|---------|
| System info | Environment check | Safe |
| Plugin manifest | Version/config | Safe |
| Dependencies | Compatibility | Safe |
| Console logs | Error messages | Review before sharing |
| Settings | Configuration | REDACT secrets |
| Vault path | Location | DO NOT share |

## Resources
- [Obsidian Bug Reports](https://forum.obsidian.md/c/bug-reports/7)
- [Plugin Developer Help](https://forum.obsidian.md/c/developers/14)
- [Obsidian Discord #plugin-dev](https://discord.gg/obsidianmd)

## Next Steps
For rate limit issues, see `obsidian-rate-limits`.

## Examples

**Basic usage**: Apply obsidian debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian debug bundle for production environments with multiple constraints and team-specific requirements.