---
name: obsidian-prod-checklist
description: |
  Pre-release plugin verification checklist for Obsidian community plugins.
  Use when preparing to release, reviewing before submission,
  or validating plugin quality before publishing.
  Trigger with phrases like "obsidian release checklist", "publish obsidian plugin",
  "obsidian plugin submission", "obsidian prod ready".
allowed-tools: Read, Grep, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Prod Checklist

## Overview
Pre-release verification for Obsidian plugins covering manifest validation, production build quality, mobile compatibility, memory leak prevention, settings migration, and community plugin submission readiness.

## Prerequisites
- Completed plugin development with all features working
- Tested in at least one vault manually
- GitHub repository with source code committed
- Node.js build toolchain configured

## Instructions

### Step 1: Validate manifest.json
```javascript
// Run: node -e '<paste this>'
const m = require('./manifest.json');

const required = ['id', 'name', 'version', 'minAppVersion', 'description', 'author'];
const missing = required.filter(f => !m[f]);
if (missing.length) {
  console.error('FAIL: Missing fields:', missing.join(', '));
  process.exit(1);
}

// id must be kebab-case, no spaces
if (!/^[a-z0-9-]+$/.test(m.id)) {
  console.error('FAIL: id must be lowercase alphanumeric with hyphens:', m.id);
  process.exit(1);
}

// minAppVersion should be a recent Obsidian version
const [major, minor] = m.minAppVersion.split('.').map(Number);
if (major < 1 || (major === 1 && minor < 4)) {
  console.warn('WARN: minAppVersion', m.minAppVersion, 'is very old — consider 1.5.0+');
}

console.log('manifest.json OK:', m.id, 'v' + m.version, '(requires Obsidian >=' + m.minAppVersion + ')');
```

### Step 2: Validate versions.json
```javascript
// Run: node -e '<paste this>'
const manifest = require('./manifest.json');
const versions = require('./versions.json');
const pkg = require('./package.json');

let fail = false;

// manifest.version should match package.json version
if (manifest.version !== pkg.version) {
  console.error('FAIL: manifest.version (' + manifest.version + ') !== package.json (' + pkg.version + ')');
  fail = true;
}

// versions.json must have an entry for current version
if (!versions[manifest.version]) {
  console.error('FAIL: versions.json missing entry for', manifest.version);
  fail = true;
} else if (versions[manifest.version] !== manifest.minAppVersion) {
  console.error('FAIL: versions.json[' + manifest.version + '] = ' +
    versions[manifest.version] + ' but manifest.minAppVersion = ' + manifest.minAppVersion);
  fail = true;
}

if (fail) process.exit(1);
console.log('versions.json OK: all versions consistent');
```

### Step 3: Production Build Checks
```bash
set -euo pipefail
# Clean build
rm -f main.js
npm ci
npm run build

# Verify main.js exists and is reasonable size
test -f main.js || { echo "FAIL: main.js not generated"; exit 1; }
SIZE=$(wc -c < main.js)
echo "main.js: $SIZE bytes"

# No inline source maps in production (increases file size significantly)
if grep -q "sourceMappingURL=data:" main.js; then
  echo "WARN: Inline sourcemaps detected — remove for production"
  echo "  Set sourcemap: false in esbuild.config.mjs"
fi

# No sourcemap file should ship
if [ -f main.js.map ]; then
  echo "WARN: main.js.map exists — exclude from release assets"
fi

# styles.css check
if [ -f styles.css ]; then
  echo "styles.css: $(wc -c < styles.css) bytes — will be included in release"
else
  echo "No styles.css (OK if plugin has no custom styles)"
fi
```

### Step 4: Code Quality — No console.log in Production
```bash
set -euo pipefail
# Obsidian reviewers reject plugins with console.log in production code
# Check source files (not the built main.js which may be minified)
HITS=$(grep -rn "console\.log\|console\.warn\|console\.info" src/ --include="*.ts" | grep -v "// DEBUG" | grep -v "\.test\." || true)

if [ -n "$HITS" ]; then
  echo "WARN: console statements found in source (remove or guard with DEBUG flag):"
  echo "$HITS"
else
  echo "OK: No unguarded console statements in src/"
fi

# Check for eval() or Function() constructor — immediate rejection
DANGEROUS=$(grep -rn "eval(\|new Function(" src/ --include="*.ts" || true)
if [ -n "$DANGEROUS" ]; then
  echo "FAIL: eval/Function() found — Obsidian team will reject this:"
  echo "$DANGEROUS"
  exit 1
fi
```

### Step 5: Memory Leak Check — Proper onunload Cleanup
Review your `main.ts` for proper resource cleanup:

```typescript
// GOOD: All resources cleaned up in onunload
export default class MyPlugin extends Plugin {
  private observer: MutationObserver | null = null;
  private intervalId: number | null = null;

  async onload() {
    // Register events via this.registerEvent — auto-cleaned
    this.registerEvent(
      this.app.workspace.on('file-open', this.handleFileOpen.bind(this))
    );

    // Register intervals via this.registerInterval — auto-cleaned
    this.intervalId = window.setInterval(() => this.sync(), 60000);
    this.registerInterval(this.intervalId);

    // DOM observers need manual cleanup
    this.observer = new MutationObserver(this.handleMutation.bind(this));
    this.observer.observe(document.body, { childList: true });
  }

  onunload() {
    // Clean up anything NOT registered via this.register*
    this.observer?.disconnect();
    this.observer = null;
  }
}
```

Common leak sources to audit:
- `setInterval` / `setTimeout` not using `this.registerInterval`
- `addEventListener` without matching `removeEventListener`
- `MutationObserver` or `ResizeObserver` without `disconnect()`
- `WebSocket` or `EventSource` connections without `close()`
- Detached DOM nodes held in class properties

### Step 6: Mobile Compatibility
```typescript
// Check if running on mobile
import { Platform } from 'obsidian';

if (Platform.isMobile) {
  // Disable features that only work on desktop
  // - No child_process or fs access
  // - No Electron APIs (clipboard, shell, dialog)
  // - Touch targets must be >= 44px
}

// If your plugin is desktop-only, set in manifest.json:
// "isDesktopOnly": true
```

Test on mobile:
1. Build and release (even a beta via BRAT)
2. Install on iOS/Android Obsidian
3. Verify: settings tab renders, commands work, no crashes on open/close
4. Check touch targets are large enough (44px minimum)

### Step 7: Settings Migration
```typescript
// Handle upgrades from older settings versions
interface MyPluginSettings {
  version: number;          // Track settings schema version
  greeting: string;
  // v2 added:
  showInStatusBar: boolean;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  version: 2,
  greeting: 'Hello!',
  showInStatusBar: true,
}

async loadSettings() {
  const saved = await this.loadData();
  this.settings = Object.assign({}, DEFAULT_SETTINGS, saved);

  // Migrate from v1 to v2
  if (!saved?.version || saved.version < 2) {
    this.settings.showInStatusBar = true;  // new default
    this.settings.version = 2;
    await this.saveSettings();
    console.log('Settings migrated to v2');
  }
}
```

### Step 8: README and Documentation
Verify your README includes:
- Clear description of what the plugin does
- Installation instructions (community plugins search + manual)
- Screenshots or GIFs of the plugin in action
- Configuration options explained
- Known limitations

```bash
set -euo pipefail
# Basic README checks
test -f README.md || { echo "FAIL: No README.md"; exit 1; }

# Check for screenshots (common requirement for discoverability)
if grep -qi "screenshot\|\.png\|\.gif\|\.jpg" README.md; then
  echo "OK: README references images"
else
  echo "WARN: No screenshots in README — strongly recommended for community listing"
fi

echo "README.md: $(wc -l < README.md) lines"
```

## Output
- Validated `manifest.json` with all required fields and correct formatting
- Consistent versions across `manifest.json`, `package.json`, and `versions.json`
- Production `main.js` without sourcemaps or debug artifacts
- Clean source code: no console.log, no eval, no dynamic code loading
- Verified `onunload()` cleanup for all registered resources
- Mobile compatibility confirmed (or `isDesktopOnly` set)
- Settings migration for users upgrading from previous versions
- README with screenshots and installation instructions

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PR rejected: missing fields | Incomplete manifest.json | Run Step 1 validation |
| PR rejected: console.log | Debug logging left in | Remove or guard with build-time flag |
| Plugin crashes on mobile | Desktop-only API used | Set `isDesktopOnly: true` or gate with `Platform.isMobile` |
| Settings lost on update | No migration logic | Implement version-based migration (Step 7) |
| Build includes sourcemaps | esbuild config | Set `sourcemap: false` for production |
| Styles not applied | Missing styles.css in release | Include in GitHub release assets |
| Old settings break new version | Schema changed | `Object.assign({}, DEFAULT_SETTINGS, saved)` handles missing keys |

## Examples

### Quick Pre-Release Validation Script
```bash
set -euo pipefail
echo "=== Obsidian Plugin Pre-Release Check ==="

# Build
npm ci && npm run build
test -f main.js || { echo "FAIL: no main.js"; exit 1; }

# Manifest
node -e "const m=require('./manifest.json'); \
  ['id','name','version','minAppVersion','description','author'].forEach(f => { \
    if(!m[f]) { console.error('MISSING:', f); process.exit(1); } \
  }); console.log('Manifest OK:', m.id, 'v'+m.version)"

# Versions
node -e "const m=require('./manifest.json'), v=require('./versions.json'); \
  if(!v[m.version]) { console.error('versions.json missing', m.version); process.exit(1); } \
  console.log('Versions OK')"

# No sourcemaps
grep -q "sourceMappingURL=data:" main.js && echo "WARN: inline sourcemaps" || echo "No sourcemaps OK"

# No console.log
COUNT=$(grep -rc "console\.\(log\|warn\|info\)" src/ --include="*.ts" 2>/dev/null | awk -F: '{s+=$2}END{print s}')
[ "$COUNT" -gt 0 ] && echo "WARN: $COUNT console statements in src/" || echo "No console OK"

echo "=== Done ==="
```

### Checklist Summary Format
After running all checks, produce a summary:
```
Pre-Release Report: my-plugin v1.2.0
  [x] manifest.json — all fields present, id=my-plugin
  [x] versions.json — 1.2.0 maps to minAppVersion 1.5.0
  [x] Build — main.js 45KB, no sourcemaps
  [x] Code quality — no console.log, no eval
  [x] Cleanup — onunload disconnects observer
  [ ] Mobile — not tested (isDesktopOnly: false)
  [x] README — has screenshots, install instructions
  [x] Settings — migration from v1 implemented
```

## Resources
- [Plugin Submission Guidelines](https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin)
- [Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Community Plugins Repo](https://github.com/obsidianmd/obsidian-releases)
- [Obsidian API Reference](https://docs.obsidian.md/Reference/TypeScript+API)

## Next Steps
For version upgrades and breaking changes, see `obsidian-upgrade-migration`.
For CI/CD automation, see `obsidian-ci-integration`.
