# Obsidian Upgrade Migration - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Check Current Compatibility
```bash
cat manifest.json | jq '.minAppVersion'


npm update obsidian
```

### Step 2: Common Migration: CodeMirror 5 to 6
```typescript
// OLD: CodeMirror 5 (Obsidian < 0.13)
// This API is deprecated
import { MarkdownView } from 'obsidian';

const view = this.app.workspace.getActiveViewOfType(MarkdownView);
const cm5 = view.sourceMode.cmEditor; // CodeMirror 5 instance

// NEW: CodeMirror 6 (Obsidian >= 0.13)
import { MarkdownView, EditorView } from 'obsidian';

const view = this.app.workspace.getActiveViewOfType(MarkdownView);
const editor = view.editor;

// For advanced CM6 access:
// @ts-ignore - internal API
const cm6: EditorView = view.editor.cm;
```

### Step 3: Settings Migration
```typescript
// Handle settings migration between plugin versions
interface PluginSettingsV1 {
  option1: string;
  option2: number;
}

interface PluginSettingsV2 {
  option1: string;
  option2: number;
  option3: boolean;  // New in v2
  settingsVersion: number;
}

const DEFAULT_SETTINGS_V2: PluginSettingsV2 = {
  option1: 'default',
  option2: 10,
  option3: true,
  settingsVersion: 2,
};

async loadSettings() {
  const data = await this.loadData();

  if (!data) {
    // Fresh install
    this.settings = { ...DEFAULT_SETTINGS_V2 };
  } else if (!data.settingsVersion || data.settingsVersion < 2) {
    // Migrate from v1 to v2
    this.settings = this.migrateSettingsV1toV2(data);
    await this.saveSettings(); // Save migrated settings
  } else {
    // Current version
    this.settings = Object.assign({}, DEFAULT_SETTINGS_V2, data);
  }
}

migrateSettingsV1toV2(v1Settings: PluginSettingsV1): PluginSettingsV2 {
  console.log('Migrating settings from v1 to v2');
  return {
    ...v1Settings,
    option3: DEFAULT_SETTINGS_V2.option3,  // Add new field with default
    settingsVersion: 2,
  };
}
```

### Step 4: Event API Migration
```typescript
// OLD: Direct event binding (memory leak risk)
this.app.workspace.on('file-open', callback);

// NEW: Registered events (auto-cleanup)
this.registerEvent(
  this.app.workspace.on('file-open', callback)
);

// OLD: Manual interval management
const interval = setInterval(() => {}, 1000);
// Must manually clear on unload

// NEW: Registered intervals (auto-cleanup)
this.registerInterval(
  window.setInterval(() => {}, 1000)
);

// OLD: DOM event listeners
document.addEventListener('click', handler);
// Must manually remove

// NEW: Registered DOM events (auto-cleanup)
this.registerDomEvent(document, 'click', handler);
```

### Step 5: Vault API Changes
```typescript
// OLD: Reading files (callback style)
this.app.vault.read(file, (content) => {
  // Handle content
});

// NEW: Reading files (Promise-based)
const content = await this.app.vault.read(file);

// OLD: Getting file by path
const file = this.app.vault.getAbstractFileByPath(path);
// Returns TAbstractFile

// NEW: Type-safe file access
const file = this.app.vault.getAbstractFileByPath(path);
if (file instanceof TFile) {
  // Safe to use as TFile
}

// NEW: Metadata cache API
// Use metadataCache for faster frontmatter access
const cache = this.app.metadataCache.getFileCache(file);
const frontmatter = cache?.frontmatter;
```

### Step 6: Editor API Migration
```typescript
// OLD: MarkdownSourceView access
const sourceView = view.sourceMode;

// NEW: Editor interface
const editor = view.editor;

// Common operations migration:

// OLD: Get selection
const selection = cm5.getSelection();

// NEW: Get selection
const selection = editor.getSelection();

// OLD: Replace selection
cm5.replaceSelection(text);

// NEW: Replace selection
editor.replaceSelection(text);

// OLD: Get cursor position
const cursor = cm5.getCursor();

// NEW: Get cursor position
const cursor = editor.getCursor();

// OLD: Set cursor
cm5.setCursor(line, ch);

// NEW: Set cursor
editor.setCursor({ line, ch });
```

### Step 7: Update Dependencies
```bash
npm install obsidian@latest --save-dev

npm update esbuild typescript

npx tsc --noEmit 2>&1 | grep -i deprecat

{
  "minAppVersion": "1.4.0"
}

{
  "1.0.0": "0.15.0",
  "2.0.0": "1.4.0"  // New version requires Obsidian 1.4+
}
```


## Complete Examples

### Version-Specific Code
```typescript
// Check Obsidian version at runtime
function supportsNewFeature(): boolean {
  const version = this.app.version;
  const [major, minor] = version.split('.').map(Number);
  return major >= 1 && minor >= 4;
}

// Use feature with fallback
if (supportsNewFeature()) {
  // Use new API
  await this.app.fileManager.processFrontMatter(file, (fm) => {
    fm['key'] = 'value';
  });
} else {
  // Fallback for older versions
  const content = await this.app.vault.read(file);
  // Manual frontmatter manipulation
}
```

### Gradual Deprecation
```typescript
// Support both old and new patterns during transition
function getEditor(view: MarkdownView): Editor {
  // Try new API first
  if (view.editor) {
    return view.editor;
  }

  // Fallback to old API (deprecated)
  // @ts-ignore
  if (view.sourceMode?.cmEditor) {
    console.warn('Using deprecated CM5 editor access');
    // @ts-ignore
    return wrapCM5Editor(view.sourceMode.cmEditor);
  }

  throw new Error('Could not get editor');
}
```


## Common Migration Scenarios

### API Version Changes
| From | To | Common Changes |
|------|-----|----------------|
| 0.x | 1.0 | Event API, Settings API |
| 1.0 | 1.1 | Editor API (CodeMirror 6) |
| 1.1 | 1.2 | Canvas API, Properties |
| 1.2+ | 1.4+ | Link resolution, Metadata |
