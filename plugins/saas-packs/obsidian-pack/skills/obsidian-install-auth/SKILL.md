---
name: obsidian-install-auth
description: |
  Set up Obsidian plugin development environment with Node.js and TypeScript.
  Use when starting a new plugin project, configuring the dev environment,
  or initializing Obsidian plugin development.
  Trigger with phrases like "obsidian setup", "obsidian plugin dev",
  "create obsidian plugin", "obsidian development environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Install & Auth

## Overview
Set up a complete Obsidian plugin development environment with TypeScript, esbuild, and hot-reload capabilities.

## Prerequisites
- Node.js 18+ (LTS recommended)
- npm or pnpm package manager
- Obsidian desktop app installed
- Git for version control
- Code editor with TypeScript support (VSCode recommended)

## Instructions

### Step 1: Clone the Sample Plugin Template
```bash
set -euo pipefail
# Clone official sample plugin
git clone https://github.com/obsidianmd/obsidian-sample-plugin.git my-obsidian-plugin
cd my-obsidian-plugin

# Remove existing git history for fresh start
rm -rf .git
git init
```

### Step 2: Install Dependencies
```bash
set -euo pipefail
# Install all dependencies
npm install

# Key dependencies included:
# - @types/node
# - typescript
# - esbuild
# - obsidian (types only - provided by Obsidian app)
```

### Step 3: Configure Development Vault
```bash
# Create a dedicated development vault
mkdir -p ~/ObsidianDev/.obsidian/plugins/my-obsidian-plugin

# Link your plugin for development
# On macOS/Linux:
ln -s "$(pwd)" ~/ObsidianDev/.obsidian/plugins/my-obsidian-plugin

# On Windows (run as admin):
# mklink /D "%USERPROFILE%\ObsidianDev\.obsidian\plugins\my-obsidian-plugin" "%CD%"
```

### Step 4: Update manifest.json
```json
{
  "id": "my-obsidian-plugin",
  "name": "My Obsidian Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "Description of your plugin",
  "author": "Your Name",
  "authorUrl": "https://your-website.com",
  "isDesktopOnly": false
}
```

### Step 5: Verify Setup
```bash
set -euo pipefail
# Build the plugin
npm run build

# Start development mode with hot-reload
npm run dev
```

## Output
- Cloned and configured plugin project
- Development vault with symlinked plugin
- Working build pipeline with esbuild
- Hot-reload enabled for rapid development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Cannot find module 'obsidian' | Types not installed | Run `npm install` again |
| Plugin not showing in Obsidian | Symlink broken | Verify symlink path, restart Obsidian |
| Build failed | TypeScript errors | Check `tsconfig.json` configuration |
| Hot-reload not working | Missing BRAT or wrong path | Install BRAT plugin or verify symlink |
| Permission denied | Symlink requires admin | Run terminal as administrator |

## Examples

### Project Structure
```
my-obsidian-plugin/
├── src/
│   └── main.ts           # Plugin entry point
├── styles.css            # Optional: Plugin styles
├── manifest.json         # Plugin metadata
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript config
├── esbuild.config.mjs    # Build configuration
└── versions.json         # Version compatibility
```

### Minimal main.ts
```typescript
import { Plugin } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    console.log('Loading My Plugin');
  }

  onunload() {
    console.log('Unloading My Plugin');
  }
}
```

## Resources
- [Obsidian Plugin Developer Docs](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin)
- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Obsidian API Reference](https://docs.obsidian.md/Reference/TypeScript+API)
- [BRAT Plugin for Development](https://github.com/TfTHacker/obsidian42-brat)

## Next Steps
After successful setup, proceed to `obsidian-hello-world` for your first plugin feature.