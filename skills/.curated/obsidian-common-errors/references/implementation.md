# Obsidian Common Errors -- Implementation Reference

## Overview

Diagnose and fix common Obsidian plugin errors including API misuse, DOM manipulation
issues, file system failures, event listener leaks, and settings corruption.

## Prerequisites

- Obsidian v1.0+ with developer tools enabled
- Node.js 18+ for plugin build toolchain
- Familiarity with Obsidian Plugin API

## Error Patterns and Fixes

### 1. Plugin Load Failure

```typescript
// Error: "Failed to load plugin: Cannot read properties of undefined (reading 'vault')"
// Cause: Accessing app.vault before plugin is fully loaded

// Bad
export default class MyPlugin extends Plugin {
    vault = this.app.vault;  // Too early

    async onload() {
        // ...
    }
}

// Good
export default class MyPlugin extends Plugin {
    async onload() {
        // Access app properties inside onload() or later
        const files = this.app.vault.getMarkdownFiles();
        console.log(`Vault has ${files.length} files`);
    }
}
```

### 2. Event Listener Leak

```typescript
// Bad: event listener registered but never cleaned up
export default class MyPlugin extends Plugin {
    async onload() {
        document.addEventListener('click', this.handleClick);
        // Memory leak -- never removed
    }
}

// Good: use registerDomEvent for automatic cleanup
export default class MyPlugin extends Plugin {
    async onload() {
        this.registerDomEvent(document, 'click', this.handleClick.bind(this));
        // Automatically removed on plugin unload
    }
}
```

### 3. Settings Load Error

```typescript
interface MySettings {
    apiKey: string;
    enableFeature: boolean;
    maxItems: number;
}

const DEFAULT_SETTINGS: MySettings = {
    apiKey: '',
    enableFeature: true,
    maxItems: 100,
};

export default class MyPlugin extends Plugin {
    settings: MySettings;

    async onload() {
        // Always merge with defaults to handle missing fields
        const saved = await this.loadData();
        this.settings = Object.assign({}, DEFAULT_SETTINGS, saved ?? {});
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }
}
```

### 4. File Read / Write Errors

```typescript
import { TFile, Notice } from 'obsidian';

async function safeReadFile(app: App, path: string): Promise<string | null> {
    const file = app.vault.getAbstractFileByPath(path);

    if (!file) {
        new Notice(`File not found: ${path}`);
        return null;
    }

    if (!(file instanceof TFile)) {
        new Notice(`Not a file: ${path}`);
        return null;
    }

    try {
        return await app.vault.read(file);
    } catch (err) {
        console.error(`Failed to read ${path}:`, err);
        new Notice(`Error reading file: ${(err as Error).message}`);
        return null;
    }
}

async function safeWriteFile(app: App, path: string, content: string): Promise<boolean> {
    try {
        const existing = app.vault.getAbstractFileByPath(path);
        if (existing instanceof TFile) {
            await app.vault.modify(existing, content);
        } else {
            await app.vault.create(path, content);
        }
        return true;
    } catch (err) {
        console.error(`Failed to write ${path}:`, err);
        new Notice(`Error writing file: ${(err as Error).message}`);
        return false;
    }
}
```

### 5. Command Palette Registration Issues

```typescript
// Bad: registering duplicate commands causes silent failures
export default class MyPlugin extends Plugin {
    async onload() {
        this.addCommand({ id: 'my-command', name: 'My Command', callback: () => {} });
        this.addCommand({ id: 'my-command', name: 'Duplicate!', callback: () => {} }); // Ignored
    }
}

// Good: use consistent, unique IDs
export default class MyPlugin extends Plugin {
    async onload() {
        this.addCommand({
            id: 'my-plugin-do-something',  // Prefix with plugin ID
            name: 'Do Something',
            hotkeys: [{ modifiers: ['Mod', 'Shift'], key: 'D' }],
            callback: () => this.doSomething(),
        });
    }
}
```

### 6. Debugging with Dev Tools

```bash
# Enable developer tools in Obsidian
# Windows/Linux: Ctrl+Shift+I
# macOS: Cmd+Option+I

# Check the console for errors:
# - "Failed to load plugin" -- check main.js exports
# - "Cannot read properties of null" -- guard against null DOM elements
# - "Maximum call stack exceeded" -- circular event handler

# Hot-reload during development
npm install -g obsidian-hot-reload
# Place .hotreload file in your plugin directory
touch /path/to/vault/.obsidian/plugins/my-plugin/.hotreload
```

### 7. Manifest Validation

```json
// .obsidian/plugins/my-plugin/manifest.json
{
    "id": "my-plugin",
    "name": "My Plugin",
    "version": "1.0.0",
    "minAppVersion": "1.0.0",
    "description": "Plugin description",
    "author": "Your Name",
    "authorUrl": "https://github.com/yourname",
    "isDesktopOnly": false
}
```

## Common Error Messages Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `Failed to load plugin` | main.js not found or syntax error | Check build output |
| `Cannot read properties of undefined` | Accessing API too early | Move to `onload()` |
| `app.vault.read is not a function` | Using old API version | Update to `vault.read(file)` |
| `Plugin already loaded` | Duplicate plugin ID | Use unique manifest.id |
| `Notice is not defined` | Missing import | `import { Notice } from 'obsidian'` |

## Resources

- [Obsidian Plugin API](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin)
- [Obsidian Developer Docs](https://docs.obsidian.md/)
- [Marcus Olsson Obsidian Plugin Dev Guide](https://marcus.se.net/obsidian-plugin-docs/)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
