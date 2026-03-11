# Obsidian Prod Checklist - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Validate manifest.json
```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "A clear, concise description (max ~250 chars)",
  "author": "Your Name",
  "authorUrl": "https://github.com/username",
  "fundingUrl": "https://buymeacoffee.com/username",
  "isDesktopOnly": false
}
```

**Validation Script:**
```bash
#!/bin/bash

MANIFEST="manifest.json"

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: manifest.json not found"
  exit 1
fi

if ! jq empty "$MANIFEST" 2>/dev/null; then
  echo "ERROR: Invalid JSON in manifest.json"
  exit 1
fi

REQUIRED=("id" "name" "version" "minAppVersion" "description" "author")
for field in "${REQUIRED[@]}"; do
  if [ "$(jq -r ".$field" "$MANIFEST")" == "null" ]; then
    echo "ERROR: Missing required field: $field"
    exit 1
  fi
done

VERSION=$(jq -r '.version' "$MANIFEST")
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Version must be valid semver: $VERSION"
  exit 1
fi

echo "manifest.json validation passed"
```

### Step 2: Validate versions.json
```json
{
  "1.0.0": "1.0.0",
  "1.0.1": "1.0.0",
  "1.1.0": "1.2.0"
}
```

Format: `"plugin-version": "minimum-obsidian-version"`

```bash
if [ ! -f "versions.json" ]; then
  echo "ERROR: versions.json not found"
  exit 1
fi

if ! jq empty "versions.json" 2>/dev/null; then
  echo "ERROR: Invalid JSON in versions.json"
  exit 1
fi

echo "versions.json validation passed"
```

### Step 3: Code Quality Checks
```bash
#!/bin/bash

echo "=== Code Quality Checks ==="

echo "Checking TypeScript..."
npm run build
if [ $? -ne 0 ]; then
  echo "ERROR: Build failed"
  exit 1
fi

echo "Running ESLint..."
npm run lint
if [ $? -ne 0 ]; then
  echo "WARNING: Linting issues found"
fi

echo "Checking for debug statements..."
CONSOLE_COUNT=$(grep -r "console.log" src/ --include="*.ts" | wc -l)
if [ "$CONSOLE_COUNT" -gt 0 ]; then
  echo "WARNING: Found $CONSOLE_COUNT console.log statements"
  grep -r "console.log" src/ --include="*.ts"
fi

echo "Checking for potential secrets..."
if grep -rE "(api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]+['\"]" src/; then
  echo "ERROR: Potential hardcoded secrets found!"
  exit 1
fi

echo "Quality checks complete"
```

### Step 4: Functionality Testing Checklist
```markdown


## Complete Examples

### Automated Release Script
```bash
#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh 1.0.0"
  exit 1
fi

npm version $VERSION --no-git-tag-version
node version-bump.mjs $VERSION

npm run build

npm test

./prepare-release.sh

echo "Ready to create GitHub release for v$VERSION"
```


## Community Plugin Requirements

### Mandatory Items
- [ ] Plugin hosted on public GitHub repository
- [ ] Valid `manifest.json` with all required fields
- [ ] Valid `versions.json` tracking compatibility
- [ ] No console errors during normal operation
- [ ] Works on all platforms (desktop: Win/Mac/Linux, mobile: iOS/Android)


## Manual Testing Checklist

### Installation
- [ ] Plugin installs correctly from .zip
- [ ] Plugin loads without errors
- [ ] Settings tab appears and functions
- [ ] All commands appear in command palette

### Core Features
- [ ] Primary feature works as expected
- [ ] Secondary features work correctly
- [ ] Settings persist after reload
- [ ] Plugin unloads cleanly

### Edge Cases
- [ ] Empty vault handling
- [ ] Large vault (1000+ files) performance
- [ ] Files with special characters in names
- [ ] Files with no frontmatter
- [ ] Files with malformed frontmatter

### Platform Testing
- [ ] Windows desktop
- [ ] macOS desktop
- [ ] Linux desktop
- [ ] iOS mobile
- [ ] Android mobile

### Compatibility
- [ ] Works with popular themes (minimal, default)
- [ ] No conflicts with common plugins
- [ ] Works in restricted mode (if applicable)
```

### Step 5: Documentation Checklist
```markdown


## README.md Requirements

### Required Sections
- [ ] Plugin name and brief description
- [ ] Installation instructions
- [ ] How to use (basic usage)
- [ ] Configuration/settings explanation
- [ ] Screenshots/demos (if visual)

### Recommended Sections
- [ ] Features list
- [ ] Changelog link
- [ ] Troubleshooting/FAQ
- [ ] Contributing guidelines
- [ ] License information

### Example Structure
```markdown

Brief description of what the plugin does.


## Features

- Feature 1
- Feature 2


## Installation

Download \`my-plugin-${VERSION}.zip\` and extract to your vault's plugins folder.
EOF

echo "Release prepared: my-plugin-${VERSION}.zip"
```

### Step 7: Submission Checklist
```markdown


## Usage

Explain how to use the plugin.


## Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Option 1 | What it does | value |


## Support

- [Report issues](link)
- [Discussions](link)
```

### Step 6: GitHub Release Preparation
```bash
#!/bin/bash

VERSION=$(jq -r '.version' manifest.json)

mkdir -p release

cp main.js manifest.json styles.css release/ 2>/dev/null

cd release
zip "../my-plugin-${VERSION}.zip" *
cd ..

cat > "release-notes-${VERSION}.md" << EOF


## What's New in v${VERSION}

### Features
- New feature description

### Bug Fixes
- Fixed issue description

### Changes
- Changed behavior description


## Community Plugin Submission

### Pre-submission
- [ ] Tested on latest Obsidian version
- [ ] No beta API features used (or documented)
- [ ] Plugin ID is unique (check existing plugins)
- [ ] README clearly explains purpose

### Repository Requirements
- [ ] Public GitHub repository
- [ ] main.js in repository root
- [ ] manifest.json in repository root
- [ ] styles.css if using styles

### Submit PR to obsidian-releases
1. Fork https://github.com/obsidianmd/obsidian-releases
2. Add entry to community-plugins.json:
```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "author": "Your Name",
  "description": "Brief description",
  "repo": "username/repo-name"
}
```
3. Create PR with description of plugin

### After Submission
- [ ] Respond to reviewer feedback promptly
- [ ] Test any requested changes
- [ ] Update PR as needed
```
