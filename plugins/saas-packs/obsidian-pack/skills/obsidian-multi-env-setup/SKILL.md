---
name: obsidian-multi-env-setup
description: |
  Configure multiple Obsidian environments for development, testing, and production.
  Use when managing separate vaults, testing plugin versions,
  or establishing a proper development workflow with isolated environments.
  Trigger with phrases like "obsidian environments", "obsidian dev vault",
  "obsidian testing setup", "multiple obsidian vaults".
allowed-tools: Read, Write, Edit, Bash(mkdir:*), Bash(ln:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Multi-Environment Setup

## Overview
Configure separate development, testing, and production environments for Obsidian plugin development with proper isolation and workflow.

## Prerequisites
- Obsidian desktop app installed
- Plugin development environment set up
- Understanding of symlinks

## Instructions

### Step 1: Create Environment Structure

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Separate development vault with symlinked plugin
- Testing vault with release builds
- Staging vault for pre-production
- Environment-specific configuration
- Test data generation scripts
- CI integration for multi-version testing

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Symlink not working | Permission denied | Run as admin (Windows) |
| Plugin not loading | Build error | Check main.js exists |
| Wrong environment | Detection failed | Check vault name/path |
| Test data missing | Script not run | Run generate-test-data |

## Resources
- [Obsidian URI Protocol](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)
- [BRAT for Beta Testing](https://github.com/TfTHacker/obsidian42-brat)

## Next Steps
For monitoring and logging, see `obsidian-observability`.
