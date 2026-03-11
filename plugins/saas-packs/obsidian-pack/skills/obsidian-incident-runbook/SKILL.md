---
name: obsidian-incident-runbook
description: |
  Troubleshoot Obsidian plugin failures with systematic incident response.
  Use when plugins crash, data is corrupted, or users report critical issues
  with your Obsidian plugin.
  Trigger with phrases like "obsidian crash", "obsidian plugin broken",
  "obsidian incident", "debug obsidian failure", "obsidian emergency".
allowed-tools: Read, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Incident Runbook

## Overview
Systematic procedures for diagnosing and resolving Obsidian plugin incidents.

## Prerequisites
- Access to affected system/vault
- Developer Console access
- Plugin source code access

## Instructions

### Step 1: Quick Triage

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Issue identified and categorized
- Diagnostic information collected
- Fix applied
- Users notified
- Post-incident review completed

## Error Handling
| Issue | Cause | Quick Fix |
|-------|-------|-----------|
| Console not opening | Obsidian crash | Start with --remote-debugging-port |
| Can't access vault | Permissions | Check file permissions |
| Plugin won't disable | Corrupt config | Edit community-plugins.json manually |
| Total crash | Memory/disk | Free up system resources |

## Resources
- [Obsidian Forum - Bug Reports](https://forum.obsidian.md/c/bug-reports/7)
- [Obsidian Discord - Help](https://discord.gg/obsidianmd)
- [Plugin Developer Documentation](https://docs.obsidian.md/Plugins)

## Next Steps
For data handling patterns, see `obsidian-data-handling`.
