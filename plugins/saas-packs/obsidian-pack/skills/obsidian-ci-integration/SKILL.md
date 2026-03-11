---
name: obsidian-ci-integration
description: |
  Set up GitHub Actions CI/CD for Obsidian plugin development.
  Use when automating builds, tests, and releases for your plugin,
  or setting up continuous integration for Obsidian projects.
  Trigger with phrases like "obsidian CI", "obsidian github actions",
  "obsidian automated build", "obsidian CI/CD".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian CI Integration

## Overview
Set up GitHub Actions for automated building, testing, and releasing Obsidian plugins.

## Prerequisites
- GitHub repository for your plugin
- Working local build (npm run build)
- Basic understanding of GitHub Actions

## Instructions

### Step 1: Create Build Workflow

### Step 2: Create Test Workflow

### Step 3: Create Release Workflow

### Step 4: Add Version Bump Script

### Step 5: Configure package.json Scripts

### Step 6: Create Validation Workflow

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Build workflow for CI validation
- Test workflow with coverage reporting
- Release workflow for automated GitHub releases
- Version bump script for consistent versioning
- Validation workflow for plugin standards

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Build fails | Missing dependencies | Ensure package-lock.json is committed |
| Release fails | Version mismatch | Run version bump before tagging |
| Upload fails | File not found | Check build output paths |
| Permission denied | Token scope | Check workflow permissions |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Obsidian Plugin Releasing Guide](https://docs.obsidian.md/Plugins/Releasing/Release+your+plugin+with+GitHub+Actions)

## Next Steps
For publishing to community plugins, see `obsidian-deploy-integration`.
