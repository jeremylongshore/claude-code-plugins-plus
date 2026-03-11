# Obsidian Local Dev Loop - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Configure Development Vault
```bash
mkdir -p ~/ObsidianDev/.obsidian/plugins
mkdir -p ~/ObsidianDev/Test\ Notes

cat > ~/ObsidianDev/Test\ Notes/Test.md << 'EOF'
This is a test note for plugin development.


## Complete Examples

### Automated Plugin Reload Script
```typescript
// src/dev-utils.ts
import { Plugin } from 'obsidian';

export function reloadPlugin(app: any, pluginId: string) {
  const plugins = app.plugins;
  return plugins.disablePlugin(pluginId)
    .then(() => plugins.enablePlugin(pluginId));
}

// Add command in main.ts (dev only):
if (process.env.NODE_ENV !== 'production') {
  this.addCommand({
    id: 'reload-plugin',
    name: 'Reload This Plugin (Dev)',
    callback: () => {
      (this.app as any).plugins.disablePlugin(this.manifest.id)
        .then(() => (this.app as any).plugins.enablePlugin(this.manifest.id));
    }
  });
}
```

### Debug Logging Utility
```typescript
// src/debug.ts
const DEBUG = process.env.NODE_ENV !== 'production';

export function debug(...args: any[]) {
  if (DEBUG) {
    console.log('[MyPlugin]', ...args);
  }
}

export function debugTime(label: string) {
  if (DEBUG) console.time(`[MyPlugin] ${label}`);
  return () => {
    if (DEBUG) console.timeEnd(`[MyPlugin] ${label}`);
  };
}
```

### VSCode Tasks
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "dev",
      "type": "npm",
      "script": "dev",
      "isBackground": true,
      "problemMatcher": {
        "pattern": {
          "regexp": "^(.*):(\\d+):(\\d+): error: (.*)$",
          "file": 1,
          "line": 2,
          "column": 3,
          "message": 4
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": ".",
          "endsPattern": "build finished"
        }
      }
    }
  ]
}
```


## Section 1

Some content here.


## Section 2

More content with [[links]] and #tags.
EOF
```

### Step 2: Link Plugin for Development
```bash
cd /path/to/my-obsidian-plugin

ln -sf "$(pwd)" ~/ObsidianDev/.obsidian/plugins/my-obsidian-plugin

ls -la ~/ObsidianDev/.obsidian/plugins/
```

### Step 3: Configure Hot-Reload with BRAT
```markdown
1. In Obsidian, go to Settings > Community plugins
2. Browse and install "BRAT" (Beta Reviewers Auto-update Tester)
3. Enable BRAT plugin
4. BRAT Settings > Enable "Auto-update plugins at startup"
5. Your plugin will auto-reload when main.js changes
```

### Step 4: Configure esbuild for Watch Mode
```javascript
// esbuild.config.mjs
import esbuild from "esbuild";
import process from "process";

const prod = process.argv[2] === "production";

const context = await esbuild.context({
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: ["obsidian", "electron", "@codemirror/*", "@lezer/*"],
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

### Step 5: Add npm Scripts
```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "node esbuild.config.mjs production",
    "test": "jest",
    "lint": "eslint src/",
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  }
}
```

### Step 6: Start Development
```bash
npm run dev

npm test -- --watch

```
