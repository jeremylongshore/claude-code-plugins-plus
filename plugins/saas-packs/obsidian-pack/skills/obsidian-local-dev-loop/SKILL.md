---
name: obsidian-local-dev-loop
description: |
  Set up a fast Obsidian plugin development loop with hot reload.
  Covers cloning the sample plugin, esbuild watch mode, symlinking
  into a vault, Ctrl+R hot reload, Chrome DevTools debugging, and
  testing with vitest. Use when starting plugin development or
  configuring a dev environment.
  Trigger with "obsidian dev loop", "obsidian hot reload",
  "obsidian development setup", "develop obsidian plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(mkdir:*), Bash(ln:*), Bash(ls:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, development, hot-reload, debugging, testing]
---

# Obsidian Local Dev Loop

## Overview

Establish a fast edit-build-test cycle for Obsidian plugins. Clone the official
sample plugin, run esbuild in watch mode, symlink into a dev vault, hot-reload
with Ctrl+R, debug with Chrome DevTools, and run tests with vitest. Aimed at
sub-second feedback from save to reload.

## Prerequisites

- Node.js 18+ with npm
- Git
- Obsidian desktop app installed
- A vault dedicated to development (keep it separate from your real notes)

## Instructions

### Step 1: Clone the official sample plugin

Start from the maintained template rather than from scratch:

```bash
set -euo pipefail

git clone https://github.com/obsidianmd/obsidian-sample-plugin.git my-plugin
cd my-plugin
rm -rf .git
git init

npm install
```

The sample includes `esbuild.config.mjs`, `tsconfig.json`, `manifest.json`, and
a working `src/main.ts`.

### Step 2: Create a dedicated dev vault

Keep a vault just for testing. Pre-populate it with sample notes.

```bash
set -euo pipefail

DEV_VAULT="$HOME/ObsidianDev"
mkdir -p "$DEV_VAULT/.obsidian/plugins"
mkdir -p "$DEV_VAULT/Test Notes"

cat > "$DEV_VAULT/Test Notes/Sample.md" << 'EOF'
---
tags: [test, sample]
---
# Sample Note

This note exists for plugin development testing.

## Section A

Some content with a [[link]] and a #tag.

## Section B

- Item 1
- Item 2
- Item 3
EOF

echo "Dev vault ready at $DEV_VAULT"
```

Open this vault in Obsidian: File > Open vault > select `~/ObsidianDev`.

### Step 3: Symlink the plugin into the dev vault

Instead of copying files after every build, symlink the entire project directory.
The build outputs `main.js` at the project root, right where Obsidian expects it.

```bash
set -euo pipefail

DEV_VAULT="$HOME/ObsidianDev"
PLUGIN_DIR="$(pwd)"
PLUGIN_ID=$(node -e "console.log(require('./manifest.json').id)")

# Symlink project root into vault plugins folder
ln -sfn "$PLUGIN_DIR" "$DEV_VAULT/.obsidian/plugins/$PLUGIN_ID"

# Verify
ls -la "$DEV_VAULT/.obsidian/plugins/$PLUGIN_ID/manifest.json"
echo "Symlinked $PLUGIN_ID into dev vault."
```

On Windows, use an admin terminal:
```powershell
mklink /D "%USERPROFILE%\ObsidianDev\.obsidian\plugins\my-plugin" "%cd%"
```

### Step 4: Run esbuild in watch mode

Watch mode rebuilds `main.js` on every source file change (typically <50ms).

```bash
npm run dev
# esbuild watches src/ and rebuilds main.js on save
# Output: "build finished" messages in the terminal
```

The `esbuild.config.mjs` from the sample plugin already supports this.
Inline source maps are enabled in dev mode for accurate stack traces.

### Step 5: Hot-reload in Obsidian

After esbuild rebuilds, reload the plugin in Obsidian:

**Method A -- Keyboard (fastest):**
Press `Ctrl+R` (or `Cmd+R` on macOS) to reload the app. This unloads all plugins
and reloads them, picking up the new `main.js`.

**Method B -- Hot Reload plugin (automatic):**
Install the [Hot Reload](https://github.com/pjeby/hot-reload) community plugin.
It watches for `main.js` changes in plugin directories and auto-reloads only the
changed plugin. No manual refresh needed.

1. In Obsidian, install "Hot Reload" from Community plugins
2. Enable it
3. Create a `.hotreload` file in your plugin directory: `touch .hotreload`
4. Now every esbuild rebuild triggers an automatic plugin reload

**Method C -- Command palette:**
Press `Ctrl+P`, type "Reload app without saving", Enter.

### Step 6: Debug with Chrome DevTools

Obsidian is an Electron app, so full Chrome DevTools are available.

1. Press `Ctrl+Shift+I` (or `Cmd+Option+I` on macOS) to open DevTools
2. **Console** tab -- see `console.log` output from your plugin
3. **Sources** tab -- set breakpoints in your code (source maps required)
4. **Network** tab -- inspect any HTTP requests your plugin makes
5. **Elements** tab -- inspect Obsidian's DOM for CSS/layout work

Tips:
- With inline source maps enabled, your TypeScript source appears in Sources > `src/main.ts`
- Use `debugger;` statements in code for precise breakpoints
- `console.log('[MyPlugin]', ...)` prefix makes filtering easy

```typescript
// Add to onload() for development:
if (process.env.NODE_ENV !== "production") {
  console.log("[MyPlugin] Dev mode active. Use Ctrl+Shift+I for DevTools.");
}
```

### Step 7: Testing with vitest

Obsidian plugins can be unit-tested by mocking the `obsidian` module.

```bash
set -euo pipefail
npm install --save-dev vitest
```

Create `vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
  },
});
```

Create a mock for the obsidian module at `__mocks__/obsidian.ts`:

```typescript
export class Plugin {
  app = {};
  loadData = vi.fn().mockResolvedValue({});
  saveData = vi.fn().mockResolvedValue(undefined);
  addCommand = vi.fn();
  addRibbonIcon = vi.fn();
  addSettingTab = vi.fn();
  addStatusBarItem = vi.fn().mockReturnValue({ setText: vi.fn() });
  registerEvent = vi.fn();
  registerInterval = vi.fn();
}

export class Notice {
  constructor(public message: string) {}
}

export class PluginSettingTab {
  containerEl = { empty: vi.fn(), createEl: vi.fn() };
  constructor(public app: any, public plugin: any) {}
  display() {}
}

export class Setting {
  constructor(el: any) {}
  setName = vi.fn().mockReturnThis();
  setDesc = vi.fn().mockReturnThis();
  addText = vi.fn().mockReturnThis();
  addToggle = vi.fn().mockReturnThis();
}

export class Modal {
  app: any;
  contentEl = { createEl: vi.fn(), empty: vi.fn() };
  constructor(app: any) { this.app = app; }
  open = vi.fn();
  close = vi.fn();
  onOpen() {}
  onClose() {}
}
```

Write a test:

```typescript
// src/__tests__/main.test.ts
import { describe, it, expect, vi } from "vitest";

vi.mock("obsidian");

describe("Plugin settings", () => {
  it("merges defaults with saved data", async () => {
    const { Plugin } = await import("obsidian");
    const { default: MyPlugin } = await import("../main");

    const plugin = new MyPlugin() as any;
    plugin.loadData = vi.fn().mockResolvedValue({ greeting: "Custom" });
    plugin.saveData = vi.fn();

    await plugin.loadSettings();

    expect(plugin.settings.greeting).toBe("Custom");
    expect(plugin.settings.showRibbon).toBe(true); // default preserved
  });
});
```

Run tests:

```bash
npx vitest run           # single run
npx vitest --watch       # watch mode alongside npm run dev
```

Add to `package.json`:

```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "node esbuild.config.mjs production",
    "test": "vitest run",
    "test:watch": "vitest --watch"
  }
}
```

## Output

After completing all steps:
- Dev vault at `~/ObsidianDev` with test notes
- Plugin symlinked into vault (no manual copying)
- `npm run dev` for sub-second rebuilds on save
- Hot Reload plugin for automatic Obsidian reload (or Ctrl+R manual)
- Chrome DevTools available via Ctrl+Shift+I with source maps
- vitest configured with obsidian mocks for unit testing
- Two-terminal workflow: terminal 1 runs `npm run dev`, terminal 2 runs `npx vitest --watch`

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Symlink not working | Permission denied (Windows) | Run terminal as Administrator |
| Plugin not in list | Symlink target wrong | Verify `ls -la` shows correct target |
| Hot Reload not triggering | Missing `.hotreload` file | `touch .hotreload` in plugin dir |
| Source maps not showing | `sourcemap: false` in config | Set `sourcemap: "inline"` for dev |
| Build not watching | Used `build` instead of `dev` | Run `npm run dev` (watch mode) |
| Tests fail with import errors | Missing vitest mock | Create `__mocks__/obsidian.ts` |
| DevTools won't open | Keyboard shortcut conflict | Use menu: View > Toggle Developer Tools |

## Examples

**Quick dev startup script** (`dev.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail

# Terminal 1: esbuild watch
npm run dev &
ESBUILD_PID=$!

# Terminal 2: vitest watch
npx vitest --watch &
VITEST_PID=$!

echo "Dev servers running. Ctrl+C to stop."
trap "kill $ESBUILD_PID $VITEST_PID" EXIT
wait
```

**VSCode task for integrated dev:**
```json
{
  "version": "2.0.0",
  "tasks": [{
    "label": "Obsidian Dev",
    "type": "npm",
    "script": "dev",
    "isBackground": true,
    "problemMatcher": {
      "pattern": { "regexp": "^x]$" },
      "background": {
        "activeOnStart": true,
        "beginsPattern": ".",
        "endsPattern": "build finished"
      }
    }
  }]
}
```

## Resources

- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Obsidian Development Workflow](https://docs.obsidian.md/Plugins/Getting+started/Development+workflow)
- [Hot Reload Plugin](https://github.com/pjeby/hot-reload)
- [esbuild Watch Mode](https://esbuild.github.io/api/#watch)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

- Build UI features: see `obsidian-core-workflow-b`
- Apply production patterns: see `obsidian-sdk-patterns`
