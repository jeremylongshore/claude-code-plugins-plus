---
name: obsidian-install-auth
description: |
  Set up Obsidian plugin development environment with Node.js and TypeScript.
  Use when starting a new plugin project, configuring the dev environment,
  or initializing Obsidian plugin development from scratch.
  Trigger with phrases like "obsidian setup", "obsidian plugin dev",
  "create obsidian plugin", "obsidian development environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*), Bash(mkdir:*), Bash(ln:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, obsidian, typescript, nodejs, setup]

---
# Obsidian Install & Auth

## Overview
Set up a complete Obsidian plugin development environment: clone the official sample plugin, install TypeScript + esbuild, configure a dev vault with symlink, verify the build pipeline, and establish the `manifest.json` / `versions.json` contract.

## Prerequisites
- Node.js 18+ (LTS recommended)
- npm or pnpm package manager
- Obsidian desktop app installed (download from https://obsidian.md)
- Git for version control

## Instructions

### Step 1: Clone the Official Sample Plugin
```bash
set -euo pipefail
# Clone the maintained template — includes esbuild, tsconfig, and a working main.ts
git clone https://github.com/obsidianmd/obsidian-sample-plugin.git my-obsidian-plugin
cd my-obsidian-plugin

# Start fresh git history
rm -rf .git
git init
git add -A
git commit -m "initial scaffold from obsidian-sample-plugin"
```

The sample plugin includes these key files:
- `esbuild.config.mjs` — bundler with watch mode and external handling
- `tsconfig.json` — TypeScript config targeting ES2018 with strict null checks
- `manifest.json` — plugin metadata Obsidian reads at load time
- `src/main.ts` — Plugin subclass with commands, settings, modal

### Step 2: Install Dependencies
```bash
set -euo pipefail
npm install

# What gets installed:
# - obsidian (type definitions only — the runtime is provided by the Obsidian app)
# - typescript
# - esbuild (fast bundler, <50ms builds)
# - @types/node
# - tslib (TypeScript helper library)
```

### Step 3: Configure manifest.json
Every Obsidian plugin requires a `manifest.json` at the project root:

```json
{
  "id": "my-obsidian-plugin",
  "name": "My Obsidian Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.5.0",
  "description": "What your plugin does in one sentence.",
  "author": "Your Name",
  "authorUrl": "https://github.com/yourname",
  "isDesktopOnly": false
}
```

Required fields: `id`, `name`, `version`, `minAppVersion`, `description`, `author`.

Rules:
- `id` must be lowercase kebab-case, match the folder name under `.obsidian/plugins/`
- `minAppVersion` should be `1.5.0` or higher (supports modern APIs like `processFrontMatter`)
- `isDesktopOnly: false` unless you use Electron-only APIs (child_process, fs, shell)

### Step 4: Create versions.json
Maps each plugin version to the minimum Obsidian version it requires:

```json
{
  "1.0.0": "1.5.0"
}
```

Obsidian uses this to warn users on older versions that they cannot install your plugin. Update it every time you bump `version` in `manifest.json`.

### Step 5: Create a Development Vault
```bash
set -euo pipefail
DEV_VAULT="$HOME/ObsidianDev"
mkdir -p "$DEV_VAULT/.obsidian/plugins"
mkdir -p "$DEV_VAULT/Test Notes"

# Create a sample note for testing
cat > "$DEV_VAULT/Test Notes/Sample.md" << 'EOF'
---
tags: [test, sample]
status: draft
---
# Sample Note

Test note for plugin development. Has [[wikilinks]], #tags, and frontmatter.

## Section A
Some content with **bold** and `inline code`.

## Section B
- [ ] Task one
- [x] Task two
- [ ] Task three
EOF

echo "Dev vault created at $DEV_VAULT"
```

Open this vault in Obsidian: File > Open vault > select `~/ObsidianDev`.

### Step 6: Symlink Plugin into Dev Vault
```bash
set -euo pipefail
DEV_VAULT="$HOME/ObsidianDev"
PLUGIN_DIR="$(pwd)"
PLUGIN_ID=$(node -e "console.log(require('./manifest.json').id)")

# Symlink project root into vault plugins folder
ln -sfn "$PLUGIN_DIR" "$DEV_VAULT/.obsidian/plugins/$PLUGIN_ID"

# Verify
ls -la "$DEV_VAULT/.obsidian/plugins/$PLUGIN_ID/manifest.json"
echo "Symlinked $PLUGIN_ID into dev vault"
```

On Windows (admin terminal):
```powershell
mklink /D "%USERPROFILE%\ObsidianDev\.obsidian\plugins\my-obsidian-plugin" "%cd%"
```

### Step 7: Build and Verify
```bash
set -euo pipefail
# Production build
npm run build
ls -la main.js manifest.json
echo "Build output: $(wc -c < main.js) bytes"

# Start dev mode with file watching
npm run dev
# esbuild watches src/ and rebuilds main.js on every save (~30ms)
```

In Obsidian:
1. Settings > Community plugins > Enable community plugins
2. Find your plugin in the list, toggle it on
3. Open Developer Console (Ctrl+Shift+I) — look for your plugin's load message
4. Press Ctrl+R to reload after any code change

### Step 8: Verify the Obsidian API is Available
```typescript
// src/main.ts — minimal verification
import { Plugin, Notice } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    // Verify core APIs are accessible
    const vaultName = this.app.vault.getName();
    const fileCount = this.app.vault.getMarkdownFiles().length;
    console.log(`[${this.manifest.id}] Loaded in vault "${vaultName}" with ${fileCount} notes`);

    this.addCommand({
      id: 'verify-setup',
      name: 'Verify Plugin Setup',
      callback: () => {
        new Notice(`Plugin working! Vault: ${vaultName}, Files: ${fileCount}`);
      },
    });
  }
}
```

## Output
- Cloned and configured plugin project with all dependencies
- `manifest.json` and `versions.json` with correct metadata
- Development vault at `~/ObsidianDev` with test notes
- Plugin symlinked into vault (no manual copying after builds)
- Working build pipeline: `npm run build` (production) and `npm run dev` (watch mode)
- Verified plugin loads and can access Vault API

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module 'obsidian'` | Types not installed | `npm install` — obsidian is a devDependency |
| Plugin not in Obsidian's list | Symlink broken or `id` mismatch | Verify symlink target exists, `id` matches folder name |
| Build fails with TypeScript errors | Strict null checks | Add null guards: `if (file instanceof TFile)` |
| Hot-reload not working | Need to reload manually | Install Hot Reload plugin or press Ctrl+R |
| Permission denied on symlink | Windows requires admin | Run terminal as Administrator |
| `main.js` not generated | Wrong esbuild entrypoint | Check `entryPoints: ["src/main.ts"]` in esbuild config |

## Examples

### Project Structure After Setup
```
my-obsidian-plugin/
├── src/
│   └── main.ts           # Plugin entry point (default export)
├── styles.css            # Optional: custom CSS (auto-loaded by Obsidian)
├── manifest.json         # Plugin metadata (required)
├── versions.json         # Version-to-minAppVersion mapping
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript config
├── esbuild.config.mjs    # Build configuration
└── main.js               # Build output (gitignored)
```

### Vault Plugin Directory Structure
```
~/ObsidianDev/
├── .obsidian/
│   ├── app.json
│   ├── community-plugins.json   # ["my-obsidian-plugin"]
│   └── plugins/
│       └── my-obsidian-plugin -> /path/to/your/project  # symlink
├── Test Notes/
│   └── Sample.md
```

### Quick Environment Check Script
```bash
set -euo pipefail
echo "Node: $(node --version)"
echo "npm: $(npm --version)"
echo "Git: $(git --version)"
echo "Obsidian vault: $(ls ~/ObsidianDev/.obsidian/app.json 2>/dev/null && echo 'found' || echo 'NOT FOUND')"
echo "Plugin symlink: $(ls -la ~/ObsidianDev/.obsidian/plugins/*/manifest.json 2>/dev/null || echo 'none')"
```

## Resources
- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin) — official starter template
- [Build a Plugin](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin) — official getting started guide
- [Obsidian API Reference](https://docs.obsidian.md/Reference/TypeScript+API) — full TypeScript API
- [BRAT Plugin](https://github.com/TfTHacker/obsidian42-brat) — beta testing distribution
- [Hot Reload Plugin](https://github.com/pjeby/hot-reload) — auto-reload on rebuild

## Next Steps
After successful setup, proceed to `obsidian-hello-world` for your first plugin feature, or `obsidian-local-dev-loop` for hot-reload development workflow.
