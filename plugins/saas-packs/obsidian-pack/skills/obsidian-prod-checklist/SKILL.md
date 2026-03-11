---
name: obsidian-prod-checklist
description: |
  Pre-release plugin verification checklist for Obsidian community plugins.
  Use when preparing to release, reviewing before submission,
  or validating plugin quality before publishing.
  Trigger with phrases like "obsidian release checklist", "publish obsidian plugin",
  "obsidian plugin submission", "obsidian prod ready".
allowed-tools: Read, Grep, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Prod Checklist

## Overview
Comprehensive pre-release checklist for submitting Obsidian plugins to the community plugin directory.

## Prerequisites
- Completed plugin development
- Tested in multiple vaults
- GitHub repository ready

## Instructions

### Step 1: Validate manifest.json

### Step 2: Validate versions.json

### Step 3: Code Quality Checks

### Step 4: Functionality Testing Checklist

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Validated manifest.json and versions.json
- Code quality verified
- Functionality tested across platforms
- Documentation complete
- Release package prepared
- Submission checklist complete

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PR rejected | Missing fields | Check all manifest fields |
| Build fails in CI | Dependencies | Lock versions in package.json |
| Plugin not found | Wrong repo path | Verify repo matches submission |
| Mobile crash | Desktop-only API | Check `isDesktopOnly` flag |

## Resources
- [Plugin Submission Guidelines](https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin)
- [Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Obsidian Releases Repo](https://github.com/obsidianmd/obsidian-releases)

## Next Steps
For version upgrades, see `obsidian-upgrade-migration`.

## Examples

**Basic usage**: Apply obsidian prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian prod checklist for production environments with multiple constraints and team-specific requirements.