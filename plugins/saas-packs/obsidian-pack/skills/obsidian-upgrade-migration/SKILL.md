---
name: obsidian-upgrade-migration
description: |
  Migrate Obsidian plugins between API versions and handle breaking changes.
  Use when upgrading to new Obsidian versions, handling API deprecations,
  or migrating plugin code to new patterns.
  Trigger with phrases like "obsidian upgrade", "obsidian migration",
  "obsidian API changes", "update obsidian plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`cat manifest.json 2>/dev/null || echo 'No manifest.json in cwd'`

## Overview
Upgrade an Obsidian plugin between versions: migrate persisted settings with version checks, replace deprecated API calls, update `manifest.json` `minAppVersion`, and test across Obsidian releases.

## Prerequisites
- Existing Obsidian plugin with source code
- Current `manifest.json` and `versions.json`
- Access to [Obsidian changelog](https://obsidian.md/changelog) and [breaking changes docs](https://docs.obsidian.md/Plugins/Releasing/Breaking+changes)
- Node.js 18+ with npm or pnpm

## Instructions

### Step 1: Audit Current Version Compatibility

Check what your plugin currently targets and what the user's Obsidian version requires:

```bash
# Current plugin target
echo "=== manifest.json ==="
cat manifest.json | python3 -c "
import json, sys
m = json.load(sys.stdin)
print(f\"Plugin: {m['id']} v{m['version']}\")
print(f\"minAppVersion: {m['minAppVersion']}\")
"

# Current obsidian type definitions
echo "=== obsidian package version ==="
npm ls obsidian 2>/dev/null || echo "Not found in node_modules"

# Check versions.json for version history
echo "=== versions.json ==="
cat versions.json 2>/dev/null | python3 -m json.tool || echo "No versions.json"
```

### Step 2: Update the Obsidian Type Definitions

```bash
# Update to latest obsidian types
npm install obsidian@latest --save-dev

# Check what changed
npm diff obsidian 2>/dev/null | head -100
```

Then check for TypeScript errors against the new types:

```bash
npx tsc --noEmit 2>&1 | head -50
```

Every error here is a breaking change you need to address.

### Step 3: Settings Migration with Version Tracking

Implement a version-aware `loadData()` pattern so existing users' settings survive upgrades:

```typescript
interface PluginSettings {
  _version: number; // Internal schema version
  // v1 fields
  enabled: boolean;
  // v2 fields (added in plugin v2.0.0)
  syncInterval: number;
  // v3 fields (added in plugin v3.0.0)
  theme: 'light' | 'dark' | 'system';
}

const CURRENT_SETTINGS_VERSION = 3;

const DEFAULT_SETTINGS: PluginSettings = {
  _version: CURRENT_SETTINGS_VERSION,
  enabled: true,
  syncInterval: 300,
  theme: 'system',
};

async loadSettings(): Promise<PluginSettings> {
  const raw = await this.loadData();
  if (!raw) return { ...DEFAULT_SETTINGS };

  const version = raw._version ?? 1;
  let settings = { ...raw };

  // v1 -> v2: add syncInterval
  if (version < 2) {
    settings.syncInterval = DEFAULT_SETTINGS.syncInterval;
    console.log('[your-plugin] Migrated settings v1 -> v2');
  }

  // v2 -> v3: add theme, rename old field
  if (version < 3) {
    settings.theme = DEFAULT_SETTINGS.theme;
    // Rename deprecated field
    if ('darkMode' in settings) {
      settings.theme = settings.darkMode ? 'dark' : 'light';
      delete settings.darkMode;
    }
    console.log('[your-plugin] Migrated settings v2 -> v3');
  }

  settings._version = CURRENT_SETTINGS_VERSION;
  await this.saveData(settings); // Persist the migration
  return settings as PluginSettings;
}
```

### Step 4: Replace Deprecated API Calls

Common deprecations and their replacements:

**Vault API changes:**
```typescript
// DEPRECATED: vault.modify with string path
await this.app.vault.modify(filePath, content);
// REPLACEMENT: use TFile object
const file = this.app.vault.getAbstractFileByPath(filePath);
if (file instanceof TFile) {
  await this.app.vault.modify(file, content);
}

// DEPRECATED: vault.create returns void in older versions
this.app.vault.create(path, content);
// REPLACEMENT: returns TFile, handle it
const newFile = await this.app.vault.create(path, content);
```

**Event registration changes:**
```typescript
// DEPRECATED: workspace.on('file-open') with old signature
this.app.workspace.on('file-open', (file) => { ... });
// REPLACEMENT: use registerEvent for proper cleanup
this.registerEvent(
  this.app.workspace.on('file-open', (file) => { ... })
);
```

**Editor API (CodeMirror 5 to 6 migration):**
```typescript
// DEPRECATED: accessing CM5 editor instance
const cm = (editor as any).cm;
cm.getValue(); // CM5

// REPLACEMENT: use Obsidian's Editor interface
const content = editor.getValue();
const cursor = editor.getCursor();
editor.replaceRange(text, cursor);

// For CM6-specific features, use EditorView extension:
import { EditorView, ViewPlugin } from '@codemirror/view';

this.registerEditorExtension(
  ViewPlugin.fromClass(class {
    constructor(view: EditorView) {
      // CM6 view access
    }
  })
);
```

**FileManager changes:**
```typescript
// DEPRECATED: processFrontMatter sync signature
this.app.fileManager.processFrontMatter(file, (fm) => {
  fm.tags = ['updated'];
});
// REPLACEMENT: async signature (Obsidian 1.4+)
await this.app.fileManager.processFrontMatter(file, (fm) => {
  fm.tags = ['updated'];
});
```

### Step 5: Update manifest.json

Bump `minAppVersion` to the lowest Obsidian version that supports all APIs you use:

```json
{
  "id": "your-plugin",
  "name": "Your Plugin",
  "version": "3.0.0",
  "minAppVersion": "1.5.0",
  "description": "...",
  "author": "...",
  "isDesktopOnly": false
}
```

Update `versions.json` to map your plugin version to the minimum Obsidian version:

```json
{
  "1.0.0": "0.15.0",
  "2.0.0": "1.0.0",
  "3.0.0": "1.5.0"
}
```

### Step 6: Test Across Obsidian Versions

Build and verify:

```bash
# Clean build
rm -rf dist node_modules/.cache
npm install
npm run build

# Check for type errors
npx tsc --noEmit

# Check bundle for leftover deprecated calls
grep -rn 'cm\.getValue\|processFrontMatter.*sync\|vault\.modify.*string' src/ || echo "No deprecated patterns found"
```

Manual testing checklist:
1. Install plugin on the `minAppVersion` you declared -- confirm it loads without errors
2. Install on latest Obsidian -- confirm full functionality
3. Test settings migration: copy a `data.json` from an older version into the plugin directory, reload, verify settings are preserved and upgraded
4. Open Developer Console (Ctrl+Shift+I) and check for deprecation warnings

### Step 7: Handle the Release

```bash
# Update version in package.json and manifest.json
npm version major  # or minor/patch

# Ensure versions.json includes the new mapping
python3 -c "
import json
v = json.load(open('versions.json'))
m = json.load(open('manifest.json'))
v[m['version']] = m['minAppVersion']
json.dump(v, open('versions.json', 'w'), indent=2)
print(f\"Added {m['version']} -> {m['minAppVersion']}\")
"

# Build the release artifacts
npm run build
```

## Output
- Updated `manifest.json` with correct `minAppVersion`
- Updated `versions.json` with new version mapping
- Settings migration code that handles all previous schema versions
- All deprecated API calls replaced with current equivalents
- Clean `tsc --noEmit` with no type errors
- Tested on minimum and latest Obsidian versions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Property does not exist on type 'Plugin'` | API removed in newer `obsidian` types | Check changelog for replacement API |
| `Cannot find module 'obsidian'` | Types not installed | `npm install obsidian@latest --save-dev` |
| Settings lost after upgrade | No migration logic for `_version` jump | Add migration step for each version gap |
| `TypeError: x is not a function` at runtime | API exists in types but not in user's Obsidian | Lower `minAppVersion` or add runtime version check |
| Plugin loads but features missing | Feature flag not migrated | Check settings migration covers all paths |

## Examples

**Simple version bump**: Plugin works fine on new Obsidian, just need to update `minAppVersion`. Run Step 1 to audit, Step 5 to update manifest, Step 6 to verify.

**CodeMirror 5 to 6 migration**: Plugin uses `editor.cm` for custom decorations. Replace CM5 `Decoration` with CM6 `EditorView` extensions per Step 4. This is the most common large migration.

**Settings schema change**: Plugin v2 renamed `darkMode: boolean` to `theme: 'light' | 'dark' | 'system'`. Add migration in Step 3 that maps the old boolean to the new enum, preserving user preference.

## Resources
- [Obsidian Changelog](https://obsidian.md/changelog)
- [Obsidian API Breaking Changes](https://docs.obsidian.md/Plugins/Releasing/Breaking+changes)
- [Obsidian Developer Docs](https://docs.obsidian.md/Plugins)
- [Obsidian Plugin API Types](https://github.com/obsidianmd/obsidian-api)
- [CodeMirror 6 Migration](https://codemirror.net/docs/migration/)

## Next Steps
For CI/CD to automate release testing, see `obsidian-ci-integration`. For multi-environment testing, see `obsidian-multi-env-setup`.
