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
Publish and distribute Obsidian plugins through the official community plugin directory. Covers the complete release workflow: building, versioning, creating GitHub releases, and submitting to the Obsidian community plugins repository for review and listing.

## Prerequisites
- Obsidian plugin with `main.ts`, `manifest.json`, and `styles.css` (if applicable)
- GitHub repository for your plugin
- Node.js build toolchain (esbuild recommended)
- Understanding of Obsidian plugin review requirements

## Instructions

### Step 1: Configure Build Pipeline
```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production",
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  }
}
```

```javascript
// esbuild.config.mjs
import esbuild from "esbuild";

const prod = process.argv[2] === "production";

await esbuild.build({
  entryPoints: ["main.ts"],
  bundle: true,
  external: ["obsidian", "electron", "@codemirror/*"],
  format: "cjs",
  target: "es2018",
  outfile: "main.js",
  sourcemap: prod ? false : "inline",
  minify: prod,
  treeShaking: true,
});
```

### Step 2: Version and Release Files
```json
// manifest.json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.4.0",
  "description": "Description of your plugin",
  "author": "Your Name",
  "isDesktopOnly": false
}
```

```json
// versions.json (maps plugin version to minimum Obsidian version)
{
  "1.0.0": "1.4.0"
}
```

### Step 3: GitHub Release Workflow
```yaml
# .github/workflows/release.yml
name: Release Plugin
on:
  push:
    tags: ["*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm run build

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            main.js
            manifest.json
            styles.css
```

### Step 4: Submit to Community Plugins
```markdown
1. Fork https://github.com/obsidianmd/obsidian-releases
2. Edit community-plugins.json, add your plugin entry:
   {
     "id": "my-plugin",
     "name": "My Plugin",
     "author": "Your Name",
     "description": "What it does",
     "repo": "username/my-plugin"
   }
3. Create a Pull Request
4. Wait for Obsidian team review (typically 1-2 weeks)
```

### Step 5: Version Bump Script
```javascript
// version-bump.mjs
import { readFileSync, writeFileSync } from "fs";

const targetVersion = process.env.npm_package_version;

// Update manifest.json
let manifest = JSON.parse(readFileSync("manifest.json", "utf8"));
const { minAppVersion } = manifest;
manifest.version = targetVersion;
writeFileSync("manifest.json", JSON.stringify(manifest, null, "\t"));

// Update versions.json
let versions = JSON.parse(readFileSync("versions.json", "utf8"));
versions[targetVersion] = minAppVersion;
writeFileSync("versions.json", JSON.stringify(versions, null, "\t"));
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Wrong manifest ID | Ensure `id` matches directory name |
| Build fails | Missing externals | Add `obsidian` to esbuild externals |
| Review rejected | Guidelines violation | Review obsidian.md/plugins/guidelines |
| Version mismatch | versions.json outdated | Run version-bump script before release |

## Examples

### Quick Release
```bash
npm version patch
git push --tags
# GitHub Actions creates the release automatically
```

## Resources
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Sample Plugin Template](https://github.com/obsidianmd/obsidian-sample-plugin)
- [Community Plugins Repo](https://github.com/obsidianmd/obsidian-releases)

## Next Steps
For event handling, see `obsidian-webhooks-events`.
