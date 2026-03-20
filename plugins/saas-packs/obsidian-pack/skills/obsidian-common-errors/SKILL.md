---
name: obsidian-common-errors
description: |
  Diagnose and fix common Obsidian plugin errors and exceptions.
  Use when encountering plugin errors, debugging failed operations,
  or troubleshooting Obsidian plugin issues.
  Trigger with phrases like "obsidian error", "fix obsidian plugin",
  "obsidian not working", "debug obsidian plugin".
allowed-tools: Read, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Common Errors

## Overview
Diagnostic guide for the six most frequent Obsidian plugin development errors, with root causes and copy-paste fixes.

## Prerequisites
- Obsidian plugin development environment set up
- Access to Developer Console (Ctrl/Cmd+Shift+I)
- Plugin source code access

## Instructions

### Step 1: "Cannot read properties of null" — Workspace Not Ready

Accessing `app.workspace.activeLeaf` or `app.workspace.getActiveViewOfType()` before the layout is initialized returns `null`.

```typescript
// BROKEN: accessing workspace immediately in onload
async onload() {
  const view = this.app.workspace.getActiveViewOfType(MarkdownView);
  // TypeError: Cannot read properties of null (reading 'editor')
  view.editor.replaceSelection('hello');
}

// FIXED: wait for layout-ready event
async onload() {
  this.app.workspace.onLayoutReady(() => {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (view) {
      view.editor.replaceSelection('hello');
    }
  });
}
```

For commands that need workspace access later (not at load time), guard with a null check:
```typescript
this.addCommand({
  id: 'my-command',
  name: 'Do Something',
  checkCallback: (checking: boolean) => {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (view) {
      if (!checking) {
        // safe to use view.editor here
        view.editor.replaceSelection('inserted');
      }
      return true;
    }
    return false;
  }
});
```

### Step 2: "Plugin failed to load" — Syntax or Manifest Errors

This error appears in the console when Obsidian cannot parse your built `main.js` or your `manifest.json` is invalid.

**Check 1: Build output exists and compiles cleanly**
```bash
set -euo pipefail
npm run build 2>&1
# Look for TypeScript errors in output
ls -la main.js  # Must exist in plugin root
```

**Check 2: manifest.json has all required fields**
```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "0.15.0",
  "description": "Does something useful",
  "author": "Your Name",
  "isDesktopOnly": false
}
```

Missing `id`, `name`, `version`, or `minAppVersion` causes a silent load failure. The `id` must match the folder name under `.obsidian/plugins/`.

**Check 3: Default export**
```typescript
// BROKEN: named export
export class MyPlugin extends Plugin { ... }

// FIXED: default export required
export default class MyPlugin extends Plugin { ... }
```

### Step 3: CSS Not Loading — Wrong styles.css Path

Obsidian auto-loads `styles.css` from the plugin root directory. It must be named exactly `styles.css` (not `style.css`, not in a subdirectory).

```bash
set -euo pipefail
# Verify all three required files exist in plugin root
ls -la styles.css manifest.json main.js
```

If you use a CSS preprocessor, ensure the build outputs to `./styles.css`:
```json
{
  "scripts": {
    "build:css": "sass src/styles.scss styles.css",
    "build": "npm run build:css && node esbuild.config.mjs"
  }
}
```

Common gotcha: the file must be `styles.css` (plural), not `style.css`.

### Step 4: Commands Not Showing in Palette

Commands registered outside `onload()` or after the plugin is enabled won't appear in the command palette.

```typescript
// BROKEN: adding command in a separate method called conditionally
async onload() {
  await this.loadSettings();
  // command never added because registerCommands is not called
}

registerCommands() {
  this.addCommand({ id: 'test', name: 'Test', callback: () => {} });
}

// FIXED: add all commands directly in onload
async onload() {
  await this.loadSettings();

  this.addCommand({
    id: 'test',
    name: 'Test',
    callback: () => {
      new Notice('Working!');
    }
  });
}
```

If a command should only be available when a markdown file is open, use `editorCallback` instead of `callback` — Obsidian automatically hides it when no editor is active:
```typescript
this.addCommand({
  id: 'editor-only',
  name: 'Editor Only Command',
  editorCallback: (editor: Editor) => {
    editor.replaceSelection('inserted text');
  }
});
```

### Step 5: Vault Read Errors — File Doesn't Exist

`vault.read()` and `vault.cachedRead()` throw if the file doesn't exist. Always check first.

```typescript
// BROKEN: assumes file exists
async readConfig() {
  const content = await this.app.vault.adapter.read('config.json');
  return JSON.parse(content);
}

// FIXED: check existence, handle missing file
async readConfig(): Promise<MyConfig> {
  const path = 'config.json';
  const exists = await this.app.vault.adapter.exists(path);
  if (!exists) {
    return { ...DEFAULT_CONFIG };
  }

  try {
    const content = await this.app.vault.adapter.read(path);
    return JSON.parse(content);
  } catch (e) {
    console.error('Failed to parse config:', e);
    return { ...DEFAULT_CONFIG };
  }
}
```

For vault files (TFile objects), use `getAbstractFileByPath`:
```typescript
const file = this.app.vault.getAbstractFileByPath('notes/target.md');
if (file instanceof TFile) {
  const content = await this.app.vault.read(file);
  // process content
} else {
  new Notice('File not found: notes/target.md');
}
```

### Step 6: Settings Not Persisting — Missing saveData Call

The most common settings bug: modifying the settings object without calling `saveData`.

```typescript
// BROKEN: settings change lost on restart
this.settings.theme = 'dark';
// forgot to call saveData!

// FIXED: always save after modifying
this.settings.theme = 'dark';
await this.saveData(this.settings);
```

In settings tabs, save on every change:
```typescript
new Setting(containerEl)
  .setName('Theme')
  .addDropdown(dropdown => dropdown
    .addOption('light', 'Light')
    .addOption('dark', 'Dark')
    .setValue(this.plugin.settings.theme)
    .onChange(async (value) => {
      this.plugin.settings.theme = value;
      await this.plugin.saveSettings();  // calls this.saveData(this.settings)
    }));
```

Load settings with defaults to prevent undefined fields after plugin updates:
```typescript
async loadSettings() {
  // loadData() returns null on first run — Object.assign handles this safely
  this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
}
```

`Object.assign` merges saved data over defaults, so new fields added in later versions get their default value instead of `undefined`.

## Output
- Identified error matched to one of the six categories
- Root cause explanation
- Working code fix applied to plugin source

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `TypeError: Cannot read properties of null` | Workspace not ready | Use `onLayoutReady` or null-check |
| `Plugin failed to load` | Build error or bad manifest | Check console, verify `manifest.json` fields |
| CSS has no effect | Wrong filename or path | Must be `styles.css` in plugin root |
| Command missing from palette | Not added in `onload()` | Move `addCommand` into `onload` |
| `Error: ENOENT` on vault read | File doesn't exist | Check with `adapter.exists()` first |
| Settings reset on restart | Missing `saveData` call | Call `saveData` after every mutation |

## Examples

### Quick Diagnostic Checklist
When a plugin fails to load, check these in order:
1. Open Developer Console (Ctrl/Cmd+Shift+I) and look for red errors
2. Verify `main.js`, `manifest.json`, and `styles.css` exist in plugin folder
3. Confirm `manifest.json` has `id`, `name`, `version`, `minAppVersion`
4. Confirm `main.ts` uses `export default class`
5. Rebuild with `npm run build` and reload Obsidian (Ctrl/Cmd+R)

### Debug Logging Pattern
```typescript
// Add to your plugin class for temporary debugging
private debug(msg: string, ...args: any[]) {
  if (this.settings.debugMode) {
    console.log(`[${this.manifest.id}] ${msg}`, ...args);
  }
}
```

## Resources
- [Obsidian Developer Docs](https://docs.obsidian.md/Plugins)
- [Obsidian Forum - Developers](https://forum.obsidian.md/c/developers/14)
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)

## Next Steps
For comprehensive debugging workflows, see `obsidian-debug-bundle`.
