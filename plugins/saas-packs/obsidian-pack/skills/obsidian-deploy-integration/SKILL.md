---
name: obsidian-deploy-integration
description: |
  Publish Obsidian plugins to the community plugin directory.
  Use when releasing your first plugin, updating existing plugins,
  or managing the community plugin submission process.
  Trigger with phrases like "publish obsidian plugin", "obsidian community plugins",
  "submit obsidian plugin", "obsidian plugin directory".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Plugin Deploy Integration

## Overview
Publish and distribute Obsidian plugins through the official community plugin directory. Covers the complete release workflow: building, versioning, creating GitHub releases, and submitting to the Obsidian community plugins repository for review and listing.

## Prerequisites
- Obsidian plugin with `main.ts`, `manifest.json`, and `styles.css` (if applicable)
- GitHub repository for your plugin
- Node.js build toolchain (esbuild recommended)
- Understanding of Obsidian plugin review requirements

## Instructions

### Step 1: Configure Build Pipeline

### Step 2: Version and Release Files

### Step 3: GitHub Release Workflow

### Step 4: Submit to Community Plugins

### Step 5: Version Bump Script

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Wrong manifest ID | Ensure `id` matches directory name |
| Build fails | Missing externals | Add `obsidian` to esbuild externals |
| Review rejected | Guidelines violation | Review obsidian.md/plugins/guidelines |
| Version mismatch | versions.json outdated | Run version-bump script before release |

## Resources
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Sample Plugin Template](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Community Plugins Repo](https://github.com/obsidianmd/obsidian-releases)

## Next Steps
For event handling, see `obsidian-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [deployment implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply obsidian deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian deploy integration for production environments with multiple constraints and team-specific requirements.