---
name: obsidian-deploy-integration
description: |
  Publish Obsidian plugins to the community plugin directory.
  Use when releasing your first plugin, updating existing plugins,
  or managing the community plugin submission process.
  Trigger with phrases like "publish obsidian plugin", "obsidian community plugins",
  "submit obsidian plugin", "obsidian plugin directory".
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Plugin Deploy Integration

## Overview
Release and distribute Obsidian plugins through multiple channels: the official community plugin directory, GitHub releases, BRAT beta testing, and manual installation. Covers the full lifecycle from building release assets to submitting your PR to the `obsidian-releases` repo.

## Prerequisites
- Obsidian plugin with `main.ts`, `manifest.json`, and `styles.css` (if applicable)
- GitHub repository for your plugin (public)
- `gh` CLI authenticated (`gh auth status`)
- Plugin passes `obsidian-prod-checklist` validation

## Instructions

### Step 1: Build Release Assets
```bash
set -euo pipefail
# Clean build for production
rm -f main.js
npm ci
npm run build

# Verify the three release files exist
for f in main.js manifest.json; do
  test -f "$f" || { echo "MISSING: $f"; exit 1; }
done
test -f styles.css && echo "styles.css included" || echo "No styles.css (OK if no custom styles)"

echo "Release assets ready"
```

### Step 2: Version Bump with version-bump.mjs
```javascript
// version-bump.mjs
import { readFileSync, writeFileSync } from 'fs';

const targetVersion = process.env.npm_package_version;

// Sync manifest.json
const manifest = JSON.parse(readFileSync('manifest.json', 'utf8'));
const { minAppVersion } = manifest;
manifest.version = targetVersion;
writeFileSync('manifest.json', JSON.stringify(manifest, null, '\t'));

// Sync versions.json — maps each plugin version to its minimum Obsidian version
const versions = JSON.parse(readFileSync('versions.json', 'utf8'));
versions[targetVersion] = minAppVersion;
writeFileSync('versions.json', JSON.stringify(versions, null, '\t'));

console.log(`Bumped to ${targetVersion} (requires Obsidian >= ${minAppVersion})`);
```

Wire it into package.json so `npm version` triggers it automatically:
```json
{
  "scripts": {
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  }
}
```

### Step 3: Create GitHub Release
```bash
set -euo pipefail
# Bump version, commit, and tag
npm version patch   # or minor / major
git push origin main --tags

# Create release with assets (or let the release workflow from obsidian-ci-integration handle it)
gh release create "$(node -p 'require("./manifest.json").version')" \
  main.js manifest.json styles.css \
  --title "v$(node -p 'require("./manifest.json").version')" \
  --generate-notes
```

The release must include these files at the root level (not nested in folders):
- `main.js` — compiled plugin code
- `manifest.json` — plugin metadata
- `styles.css` — only if your plugin has custom styles

### Step 4: Submit to Community Plugins
First-time submission requires a PR to the [obsidian-releases](https://github.com/obsidianmd/obsidian-releases) repo:

```bash
set -euo pipefail
# Fork and clone the releases repo
gh repo fork obsidianmd/obsidian-releases --clone
cd obsidian-releases

# Add your plugin entry to community-plugins.json
node -e "
  const fs = require('fs');
  const plugins = JSON.parse(fs.readFileSync('community-plugins.json', 'utf8'));
  const entry = {
    id: 'your-plugin-id',
    name: 'Your Plugin Name',
    author: 'Your Name',
    description: 'Brief description of what your plugin does.',
    repo: 'your-github-username/your-plugin-repo'
  };

  // Insert alphabetically by id
  const idx = plugins.findIndex(p => p.id.localeCompare(entry.id) > 0);
  plugins.splice(idx >= 0 ? idx : plugins.length, 0, entry);
  fs.writeFileSync('community-plugins.json', JSON.stringify(plugins, null, '\t') + '\n');
  console.log('Added', entry.id, 'at index', idx >= 0 ? idx : plugins.length);
"

git checkout -b add-your-plugin-id
git add community-plugins.json
git commit -m "Add your-plugin-id"
git push origin add-your-plugin-id
gh pr create --repo obsidianmd/obsidian-releases \
  --title "Add your-plugin-id" \
  --body "## Plugin submission

- **Repo:** https://github.com/your-username/your-plugin-repo
- **Description:** Brief description
- **I have tested on:** Desktop (macOS/Windows/Linux), Mobile (iOS/Android)"
```

Review requirements the Obsidian team checks:
- `manifest.json` has all required fields (`id`, `name`, `version`, `minAppVersion`, `description`, `author`)
- `id` in manifest matches the `id` in your community-plugins.json entry
- No `console.log` in production code
- No `eval()` or dynamic code execution
- No remote code loading at runtime
- Plugin works on mobile if `isDesktopOnly` is not set

### Step 5: BRAT for Beta Testing
Before submitting to community plugins, test your distribution via [BRAT](https://github.com/TfTHacker/obsidian42-brat):

1. Users install BRAT from community plugins
2. In BRAT settings, they click "Add Beta Plugin"
3. They enter your GitHub repo URL: `your-username/your-plugin-repo`
4. BRAT installs the latest release (including pre-releases)

To push a beta:
```bash
set -euo pipefail
npm version prerelease --preid=beta
git push origin main --tags
gh release create "$(node -p 'require("./manifest.json").version')" \
  main.js manifest.json styles.css \
  --title "Beta: v$(node -p 'require("./manifest.json").version')" \
  --prerelease
```

### Step 6: Manual Installation
For users who prefer manual install or for testing outside BRAT:

```bash
set -euo pipefail
# Users copy files to their vault's plugin directory
VAULT_PATH="/path/to/vault"
PLUGIN_ID="your-plugin-id"
DEST="$VAULT_PATH/.obsidian/plugins/$PLUGIN_ID"

mkdir -p "$DEST"
cp main.js manifest.json "$DEST/"
test -f styles.css && cp styles.css "$DEST/"

echo "Installed to $DEST — restart Obsidian and enable in Settings > Community Plugins"
```

## Output
- Production `main.js`, `manifest.json`, and `styles.css` as GitHub release assets
- `version-bump.mjs` script for consistent versioning across all config files
- PR to `obsidianmd/obsidian-releases` for community plugin listing
- BRAT-compatible releases for beta testing
- Manual install path for direct distribution

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not loading after install | `id` in manifest doesn't match directory name | Ensure the plugin folder name matches `manifest.json` `id` |
| Build output missing | esbuild `outfile` misconfigured | Set `outfile: 'main.js'` in esbuild config |
| Community PR rejected | Guidelines violation | Check [Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines) |
| Version mismatch | Forgot to run version-bump | Use `npm version` which triggers the script automatically |
| BRAT can't find releases | No GitHub release created | BRAT needs actual GitHub releases, not just tags |
| `gh release create` fails | Not authenticated | Run `gh auth login` first |
| Manual install doesn't load | Missing `manifest.json` | All three files must be in the plugin directory |

## Examples

### Update an Existing Community Plugin
Already listed? Just create a new release — Obsidian auto-detects new versions:
```bash
set -euo pipefail
npm version patch
git push origin main --tags
# Release workflow creates the GitHub release automatically
```
Users see the update in Settings > Community Plugins > Check for updates.

### Check Your Submission Status
```bash
set -euo pipefail
# See if your plugin is already in the directory
gh pr list --repo obsidianmd/obsidian-releases --search "your-plugin-id" --state all
```

## Resources
- [Obsidian Plugin Submission Guide](https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin)
- [Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Community Plugins Repo](https://github.com/obsidianmd/obsidian-releases)
- [BRAT Plugin](https://github.com/TfTHacker/obsidian42-brat)
- [Sample Plugin Template](https://github.com/obsidianmd/obsidian-sample-plugin)

## Next Steps
For event handling patterns, see `obsidian-webhooks-events`.
For pre-release quality validation, see `obsidian-prod-checklist`.
