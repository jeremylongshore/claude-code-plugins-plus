---
name: obsidian-core-workflow-a
description: |
  Create an Obsidian plugin from scratch with full project scaffolding.
  Covers Plugin class, ribbon icons, commands, settings tab, esbuild config,
  manifest.json, and building/testing. Use when starting a new plugin,
  scaffolding a project, or learning the plugin lifecycle.
  Trigger with "create obsidian plugin", "scaffold obsidian plugin",
  "new obsidian plugin", "obsidian plugin from scratch".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(mkdir:*), Bash(ln:*), Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, plugin-development, typescript, scaffolding]
---

# Obsidian Core Workflow A: Create a Plugin from Scratch

## Overview

Build a complete Obsidian plugin from an empty directory. By the end you will have a
working plugin with a ribbon icon, command palette entries, a settings tab, and a
production esbuild build. Every file is shown in full -- no stubs.

## Prerequisites

- Node.js 18+ installed
- Obsidian desktop app installed
- A vault to test in (create a fresh vault at `~/ObsidianDev` if needed)

## Instructions

### Step 1: Scaffold the project

```bash
set -euo pipefail

PLUGIN_NAME="my-obsidian-plugin"
mkdir -p "$PLUGIN_NAME/src"
cd "$PLUGIN_NAME"

# Initialize Node project
npm init -y

# Install Obsidian types and build tool
npm install --save-dev obsidian@latest typescript@latest esbuild@latest \
  @types/node@latest tslib@latest

# TypeScript config
cat > tsconfig.json << 'TSEOF'
{
  "compilerOptions": {
    "baseUrl": ".",
    "inlineSourceMap": true,
    "inlineSources": true,
    "module": "ESNext",
    "target": "ES2018",
    "allowJs": true,
    "noImplicitAny": true,
    "moduleResolution": "node",
    "importHelpers": true,
    "isolatedModules": true,
    "strictNullChecks": true,
    "lib": ["DOM", "ES2018", "ES2021.String"]
  },
  "include": ["src/**/*.ts"]
}
TSEOF

echo "Scaffolding complete."
```

### Step 2: Create manifest.json

Every Obsidian plugin needs a `manifest.json` at the project root. This is what
Obsidian reads to register the plugin.

```json
{
  "id": "my-obsidian-plugin",
  "name": "My Obsidian Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "A starter Obsidian plugin.",
  "author": "Your Name",
  "isDesktopOnly": false
}
```

### Step 3: Write the esbuild config

```javascript
// esbuild.config.mjs
import esbuild from "esbuild";
import process from "process";

const prod = process.argv[2] === "production";

const context = await esbuild.context({
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: [
    "obsidian",
    "electron",
    "@codemirror/autocomplete",
    "@codemirror/collab",
    "@codemirror/commands",
    "@codemirror/language",
    "@codemirror/lint",
    "@codemirror/search",
    "@codemirror/state",
    "@codemirror/view",
    "@lezer/common",
    "@lezer/highlight",
    "@lezer/lr",
  ],
  format: "cjs",
  target: "es2018",
  logLevel: "info",
  sourcemap: prod ? false : "inline",
  treeShaking: true,
  outfile: "main.js",
});

if (prod) {
  await context.rebuild();
  process.exit(0);
} else {
  await context.watch();
}
```

### Step 4: Write main.ts -- the full plugin

This single file contains the Plugin subclass, a settings interface with defaults,
a settings tab, and three commands.

```typescript
// src/main.ts
import {
  App,
  Editor,
  MarkdownView,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
} from "obsidian";

// ── Settings ────────────────────────────────────────────────────────
interface MyPluginSettings {
  greeting: string;
  showRibbon: boolean;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  greeting: "Hello from My Plugin!",
  showRibbon: true,
};

// ── Plugin ──────────────────────────────────────────────────────────
export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;

  async onload() {
    await this.loadSettings();

    // Ribbon icon -- shows a Notice when clicked
    if (this.settings.showRibbon) {
      this.addRibbonIcon("sparkles", "My Plugin: Greet", () => {
        new Notice(this.settings.greeting);
      });
    }

    // Command: show greeting as Notice
    this.addCommand({
      id: "show-greeting",
      name: "Show greeting",
      callback: () => {
        new Notice(this.settings.greeting);
      },
    });

    // Command: insert greeting at cursor (only available in editor)
    this.addCommand({
      id: "insert-greeting",
      name: "Insert greeting at cursor",
      editorCallback: (editor: Editor, view: MarkdownView) => {
        editor.replaceSelection(this.settings.greeting);
      },
    });

    // Command: count words in current note
    this.addCommand({
      id: "count-words",
      name: "Count words in current note",
      editorCallback: (editor: Editor) => {
        const text = editor.getValue();
        const count = text.split(/\s+/).filter(Boolean).length;
        new Notice(`Word count: ${count}`);
      },
    });

    // Status bar item
    const statusEl = this.addStatusBarItem();
    statusEl.setText("Plugin loaded");

    // Settings tab
    this.addSettingTab(new MyPluginSettingTab(this.app, this));

    console.log("MyPlugin loaded");
  }

  onunload() {
    console.log("MyPlugin unloaded");
  }

  async loadSettings() {
    this.settings = Object.assign(
      {},
      DEFAULT_SETTINGS,
      await this.loadData()
    );
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

// ── Settings Tab ────────────────────────────────────────────────────
class MyPluginSettingTab extends PluginSettingTab {
  plugin: MyPlugin;

  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName("Greeting message")
      .setDesc("Text shown by the greet command and ribbon icon.")
      .addText((text) =>
        text
          .setPlaceholder("Hello from My Plugin!")
          .setValue(this.plugin.settings.greeting)
          .onChange(async (value) => {
            this.plugin.settings.greeting = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Show ribbon icon")
      .setDesc("Toggle the sparkles icon in the left ribbon.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.showRibbon)
          .onChange(async (value) => {
            this.plugin.settings.showRibbon = value;
            await this.plugin.saveSettings();
            new Notice("Reload plugin to apply ribbon change.");
          })
      );
  }
}
```

### Step 5: Add npm scripts and build

Add these scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "node esbuild.config.mjs production"
  }
}
```

Build the plugin:

```bash
set -euo pipefail
npm run build
# Output: main.js at project root
ls -la main.js manifest.json
```

### Step 6: Install into your vault and test

```bash
set -euo pipefail

VAULT="$HOME/ObsidianDev"
PLUGIN_ID="my-obsidian-plugin"

# Create plugin directory in vault
mkdir -p "$VAULT/.obsidian/plugins/$PLUGIN_ID"

# Copy build artifacts
cp main.js manifest.json "$VAULT/.obsidian/plugins/$PLUGIN_ID/"

echo "Plugin installed. Open Obsidian, enable it in Settings > Community plugins."
```

In Obsidian:
1. Settings > Community plugins > Enable community plugins
2. Find "My Obsidian Plugin" in the list, toggle it on
3. Click the sparkles icon in the left ribbon
4. Open command palette (Ctrl/Cmd+P), search "Show greeting"
5. Open Settings > My Obsidian Plugin to change the greeting text

## Output

A complete plugin directory containing:
- `manifest.json` -- plugin metadata Obsidian reads
- `src/main.ts` -- Plugin subclass with commands, ribbon icon, settings tab
- `esbuild.config.mjs` -- bundler with watch mode support
- `main.js` -- production build output
- `package.json` + `tsconfig.json` -- standard Node/TS project files

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'obsidian'` | Missing dev dependency | `npm install --save-dev obsidian` |
| Plugin not in list | `manifest.json` missing or invalid | Verify `id` field matches folder name |
| Ribbon icon missing | Invalid icon name | Use a Lucide icon name (sparkles, file-text, search, etc.) |
| Settings not persisting | Forgot `await this.saveData()` | Always await `saveData` in onChange |
| `editorCallback` command greyed out | No active editor | Open a markdown note first |
| Build fails with external error | Forgot to externalize obsidian | Check `external` array in esbuild config |

## Examples

**Minimal manifest.json for community submission:**
```json
{
  "id": "my-obsidian-plugin",
  "name": "My Obsidian Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "Does one useful thing.",
  "author": "Your Name",
  "authorUrl": "https://github.com/yourname",
  "isDesktopOnly": false
}
```

**Adding a hotkey-enabled command:**
```typescript
this.addCommand({
  id: "toggle-sidebar",
  name: "Toggle custom sidebar",
  // Users can assign a hotkey in Settings > Hotkeys
  callback: () => this.toggleSidebar(),
});
```

## Resources

- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin) -- official starter
- [Obsidian Plugin API Reference](https://docs.obsidian.md/Reference/TypeScript+API)
- [Lucide Icons](https://lucide.dev/icons/) -- icon names for `addRibbonIcon`
- [esbuild Documentation](https://esbuild.github.io/)

## Next Steps

- Add custom views and modals: see `obsidian-core-workflow-b`
- Set up hot-reload development: see `obsidian-local-dev-loop`
- Apply production patterns: see `obsidian-sdk-patterns`
