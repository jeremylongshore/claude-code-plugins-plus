# Obsidian CI Integration - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Create Build Workflow
```yaml
name: Build Obsidian Plugin

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint
        continue-on-error: true

      - name: Type check
        run: npm run typecheck
        if: always()

      - name: Build
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: plugin-build
          path: |
            main.js
            manifest.json
            styles.css
          if-no-files-found: error
```

### Step 2: Create Test Workflow
```yaml
name: Test

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: false
```

### Step 3: Create Release Workflow
```yaml
name: Release Obsidian Plugin

on:
  push:
    tags:
      - '*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Get version
        id: version
        run: echo "version=$(jq -r '.version' manifest.json)" >> $GITHUB_OUTPUT

      - name: Verify tag matches version
        run: |
          TAG_VERSION="${GITHUB_REF#refs/tags/}"
          MANIFEST_VERSION="${{ steps.version.outputs.version }}"
          if [ "$TAG_VERSION" != "$MANIFEST_VERSION" ]; then
            echo "Tag ($TAG_VERSION) does not match manifest version ($MANIFEST_VERSION)"
            exit 1
          fi

      - name: Create release archive
        run: |
          mkdir release
          cp main.js manifest.json release/
          [ -f styles.css ] && cp styles.css release/
          cd release && zip -r ../my-plugin-${{ steps.version.outputs.version }}.zip *

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            main.js
            manifest.json
            styles.css
            my-plugin-${{ steps.version.outputs.version }}.zip
          generate_release_notes: true
          draft: false
          prerelease: false
```

### Step 4: Add Version Bump Script
```javascript
// version-bump.mjs
import { readFileSync, writeFileSync } from "fs";

const targetVersion = process.argv[2];
if (!targetVersion) {
  console.error("Usage: node version-bump.mjs <version>");
  process.exit(1);
}

// Validate semver
if (!/^\d+\.\d+\.\d+$/.test(targetVersion)) {
  console.error("Invalid version format. Use semver: x.y.z");
  process.exit(1);
}

// Update manifest.json
const manifest = JSON.parse(readFileSync("manifest.json", "utf8"));
const { minAppVersion } = manifest;
manifest.version = targetVersion;
writeFileSync("manifest.json", JSON.stringify(manifest, null, "\t"));

// Update versions.json
let versions = {};
try {
  versions = JSON.parse(readFileSync("versions.json", "utf8"));
} catch {
  // File doesn't exist, create new
}
versions[targetVersion] = minAppVersion;
writeFileSync("versions.json", JSON.stringify(versions, null, "\t"));

// Update package.json
const pkg = JSON.parse(readFileSync("package.json", "utf8"));
pkg.version = targetVersion;
writeFileSync("package.json", JSON.stringify(pkg, null, "\t"));

console.log(`Version bumped to ${targetVersion}`);
```

### Step 5: Configure package.json Scripts
```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "node esbuild.config.mjs production",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src/ --ext .ts",
    "typecheck": "tsc --noEmit",
    "version": "node version-bump.mjs && git add manifest.json versions.json package.json",
    "release": "npm run version && git commit -m 'Bump version' && git push && git push --tags"
  }
}
```

### Step 6: Create Validation Workflow
```yaml
name: Validate Plugin

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validate manifest.json
        run: |
          # Check required fields
          for field in id name version minAppVersion description author; do
            value=$(jq -r ".$field" manifest.json)
            if [ "$value" == "null" ] || [ -z "$value" ]; then
              echo "ERROR: Missing required field: $field"
              exit 1
            fi
          done

          # Validate version format
          version=$(jq -r '.version' manifest.json)
          if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "ERROR: Invalid version format: $version"
            exit 1
          fi

          echo "manifest.json is valid"

      - name: Validate versions.json
        run: |
          if [ ! -f versions.json ]; then
            echo "ERROR: versions.json not found"
            exit 1
          fi

          # Validate JSON syntax
          if ! jq empty versions.json; then
            echo "ERROR: Invalid JSON in versions.json"
            exit 1
          fi

          # Check current version is in versions.json
          current=$(jq -r '.version' manifest.json)
          if [ "$(jq -r ".[\"$current\"]" versions.json)" == "null" ]; then
            echo "WARNING: Current version $current not in versions.json"
          fi

          echo "versions.json is valid"

      - name: Check for console.log
        run: |
          count=$(grep -r "console.log" src/ --include="*.ts" | wc -l || true)
          if [ "$count" -gt 5 ]; then
            echo "WARNING: Found $count console.log statements (consider removing before release)"
          fi
```


## Complete Examples

### Manual Release Process
```bash
npm run version 1.0.1

git add -A
git commit -m "Release v1.0.1"
git tag 1.0.1

git push && git push --tags
```

### Beta Release Workflow
```yaml
name: Beta Release

on:
  push:
    branches: [beta]

jobs:
  beta:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build

      - name: Create beta release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: beta
          prerelease: true
          files: |
            main.js
            manifest.json
          body: |
            Beta release from ${{ github.sha }}
            Install via BRAT: `username/repo-name` with beta tag
```
