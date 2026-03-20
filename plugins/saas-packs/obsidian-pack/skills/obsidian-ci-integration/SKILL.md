---
name: obsidian-ci-integration
description: |
  Set up GitHub Actions CI/CD for Obsidian plugin development.
  Use when automating builds, tests, and releases for your plugin,
  or setting up continuous integration for Obsidian projects.
  Trigger with phrases like "obsidian CI", "obsidian github actions",
  "obsidian automated build", "obsidian CI/CD".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian CI Integration

## Overview
GitHub Actions workflows for Obsidian plugin development: build validation on every push, automated releases when you tag, version-bump scripting, manifest.json validation, and BRAT beta channel support.

## Prerequisites
- GitHub repository with an Obsidian plugin
- Working local build (`npm run build` produces `main.js`)
- `manifest.json` and `versions.json` in repo root
- GitHub Actions enabled on the repository

## Instructions

### Step 1: Create Build Workflow
```yaml
# .github/workflows/build.yml
name: Build Plugin
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Build plugin
        run: npm run build

      - name: Verify build output
        run: |
          if [ ! -f main.js ]; then
            echo "ERROR: main.js not found after build"
            exit 1
          fi
          echo "main.js size: $(wc -c < main.js) bytes"

      - name: Validate manifest.json
        run: |
          node -e "
            const m = require('./manifest.json');
            const required = ['id', 'name', 'version', 'minAppVersion', 'description', 'author'];
            const missing = required.filter(f => !m[f]);
            if (missing.length) {
              console.error('Missing manifest fields:', missing.join(', '));
              process.exit(1);
            }
            console.log('manifest.json valid:', m.id, 'v' + m.version);
          "
```

### Step 2: Create Release Workflow
```yaml
# .github/workflows/release.yml
name: Release Plugin
on:
  push:
    tags:
      - '*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - run: npm ci
      - run: npm run build

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            main.js
            manifest.json
            styles.css
          draft: false
          generate_release_notes: true
```

### Step 3: Create Version Bump Script
```javascript
// version-bump.mjs
import { readFileSync, writeFileSync } from 'fs';

const targetVersion = process.env.npm_package_version;

// Update manifest.json
const manifest = JSON.parse(readFileSync('manifest.json', 'utf8'));
const { minAppVersion } = manifest;
manifest.version = targetVersion;
writeFileSync('manifest.json', JSON.stringify(manifest, null, '\t'));

// Update versions.json — maps plugin version to minimum Obsidian version
const versions = JSON.parse(readFileSync('versions.json', 'utf8'));
versions[targetVersion] = minAppVersion;
writeFileSync('versions.json', JSON.stringify(versions, null, '\t'));

console.log(`Bumped to ${targetVersion} (minAppVersion: ${minAppVersion})`);
```

### Step 4: Wire Version Bump into package.json
```json
{
  "scripts": {
    "build": "node esbuild.config.mjs",
    "dev": "node esbuild.config.mjs --watch",
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  }
}
```

Now `npm version patch` (or minor/major) runs the bump script automatically.

### Step 5: Add Manifest Validation Workflow
```yaml
# .github/workflows/validate.yml
name: Validate Plugin
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check manifest/versions consistency
        run: |
          node -e "
            const manifest = require('./manifest.json');
            const versions = require('./versions.json');
            const pkg = require('./package.json');
            let fail = false;

            if (manifest.version !== pkg.version) {
              console.error('Version mismatch: manifest=' + manifest.version + ' package=' + pkg.version);
              fail = true;
            }

            if (!versions[manifest.version]) {
              console.error('versions.json missing entry for ' + manifest.version);
              fail = true;
            }

            if (fail) process.exit(1);
            console.log('All versions consistent: ' + manifest.version);
          "
```

### Step 6: BRAT Beta Support
Add a `beta-manifest.json` for [BRAT](https://github.com/TfTHacker/obsidian42-brat) beta testers:
```json
{
  "id": "your-plugin-id",
  "name": "Your Plugin (Beta)",
  "version": "1.2.0-beta.1",
  "minAppVersion": "1.5.0",
  "description": "Beta channel — install via BRAT",
  "author": "Your Name"
}
```

Beta users install via BRAT by entering your GitHub repo URL. BRAT fetches the latest release (including pre-releases) automatically — no submission to the community repo needed.

## Output
- `.github/workflows/build.yml` — validates build on every push/PR
- `.github/workflows/release.yml` — creates GitHub release with `main.js`, `manifest.json`, `styles.css` on tag push
- `.github/workflows/validate.yml` — checks version consistency across manifest, package.json, and versions.json
- `version-bump.mjs` — keeps manifest.json and versions.json in sync with package.json version
- Optional `beta-manifest.json` for BRAT beta channel

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `main.js not found` | Build script doesn't output to root | Check esbuild `outfile` points to `./main.js` |
| Release has no assets | Tag pushed before build | Let the release workflow handle the build, don't attach manually |
| Version mismatch | Forgot `npm version` | Run `npm version patch` instead of editing manifest by hand |
| BRAT not picking up beta | No pre-release on GitHub | Create release and check "pre-release" checkbox |
| `npm ci` fails | No lockfile | Commit `package-lock.json` to the repo |
| Permission denied on release | Missing `contents: write` | Add `permissions` block to release job |

## Examples

### Tag and Release a New Version
```bash
set -euo pipefail
# Bump, commit, tag, push — release workflow fires automatically
npm version patch
git push origin main --tags
```

### Manual Build Verification
```bash
set -euo pipefail
npm ci
npm run build
test -f main.js && echo "Build OK: $(wc -c < main.js) bytes" || echo "FAIL: main.js missing"
node -e "const m=require('./manifest.json'); console.log(m.id, 'v'+m.version)"
```

### Release with Changelog
```yaml
# In release.yml, replace generate_release_notes with a body:
- name: Create GitHub Release
  uses: softprops/action-gh-release@v2
  with:
    files: |
      main.js
      manifest.json
      styles.css
    body: |
      ## Changes
      - Feature: Added X
      - Fix: Resolved Y
```

## Resources
- [Obsidian Plugin Releasing Guide](https://docs.obsidian.md/Plugins/Releasing/Release+your+plugin+with+GitHub+Actions)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [BRAT Plugin](https://github.com/TfTHacker/obsidian42-brat)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)

## Next Steps
For publishing to the community plugin directory, see `obsidian-deploy-integration`.
For pre-release quality checks, see `obsidian-prod-checklist`.
