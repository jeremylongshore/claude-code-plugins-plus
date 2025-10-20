---
name: Marketplace Manager
description: Automatically manages marketplace catalog updates, syncs marketplace.json, and handles plugin distribution when user mentions marketplace update, sync catalog, or add to marketplace. Specific to claude-code-plugins two-catalog system.
allowed-tools: Read, Write, Edit, Grep, Bash
---

# Marketplace Manager

## Purpose
Automatically manages the claude-code-plugins marketplace catalog system, handling updates to marketplace.extended.json, syncing to marketplace.json, and ensuring catalog integrity.

## Trigger Keywords
- "update marketplace"
- "sync marketplace" or "sync catalog"
- "add to marketplace"
- "marketplace catalog"
- "update catalog"
- "regenerate marketplace"

## Two-Catalog System

**Critical Understanding:**
```
marketplace.extended.json (SOURCE OF TRUTH)
├── Full metadata
├── Extended fields (featured, mcpTools, etc.)
└── Edit THIS file manually

↓ npm run sync-marketplace

marketplace.json (GENERATED)
├── CLI-compatible subset
├── Sanitized fields
└── NEVER edit directly
```

## Marketplace Management Tasks

### 1. Add Plugin to Catalog

When adding new plugin:

```json
// Add to marketplace.extended.json
{
  "name": "plugin-name",
  "source": "./plugins/category/plugin-name",
  "description": "Clear one-line description",
  "version": "1.0.0",
  "category": "productivity",
  "keywords": ["keyword1", "keyword2"],
  "author": {
    "name": "Author Name",
    "email": "[email protected]"
  },
  "repository": "https://github.com/user/repo",
  "featured": false  // true for featured plugins
}
```

Then:
```bash
npm run sync-marketplace
```

### 2. Update Plugin Version

When bumping version:

1. Update `plugins/category/plugin-name/.claude-plugin/plugin.json`
2. Update marketplace.extended.json entry
3. Run `npm run sync-marketplace`
4. Validate sync worked: `git diff .claude-plugin/marketplace.json`

### 3. Sync Validation

After sync, verify:
```bash
# Check marketplace.json was regenerated
git status .claude-plugin/marketplace.json

# Validate JSON syntax
jq empty .claude-plugin/marketplace.extended.json
jq empty .claude-plugin/marketplace.json

# Check specific plugin entry
jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.json
```

### 4. Featured Plugin Management

Mark plugin as featured:
```json
{
  "name": "plugin-name",
  "featured": true,  // Add this field
  // ... rest of fields
}
```

Featured plugins appear first in marketplace.

### 5. Catalog Integrity Checks

I automatically verify:
- ✅ No duplicate plugin names
- ✅ All source paths exist
- ✅ All plugins have required fields
- ✅ Versions are semantic (x.y.z)
- ✅ Categories are valid
- ✅ JSON is valid
- ✅ Sync is current (no uncommitted changes to marketplace.json)

## Valid Categories

```
productivity, security, testing, deployment, documentation,
analysis, integration, ai, devops, debugging, code-quality,
design, example, api-development, database, crypto,
performance, ai-ml, other
```

## Sync Process

When I sync marketplace:

1. **Backup Current State**
   ```bash
   cp .claude-plugin/marketplace.json .claude-plugin/marketplace.json.backup
   ```

2. **Run Sync Script**
   ```bash
   npm run sync-marketplace
   # or: node scripts/sync-marketplace.cjs
   ```

3. **Validate Output**
   ```bash
   # Check sync success
   jq empty .claude-plugin/marketplace.json

   # Verify plugins count
   jq '.plugins | length' .claude-plugin/marketplace.json
   ```

4. **Check Diff**
   ```bash
   git diff .claude-plugin/marketplace.json
   ```

5. **Commit if Valid**
   ```bash
   git add .claude-plugin/marketplace.extended.json .claude-plugin/marketplace.json
   git commit -m "chore: Update marketplace catalog"
   ```

## Sanitized Fields

These fields are REMOVED from marketplace.json (CLI):
- `featured` - Extended metadata
- `mcpTools` - Extended metadata
- `pluginCount` - Extended metadata
- `pricing` - Extended metadata
- `components` - Extended metadata

**Only add these to marketplace.extended.json**

## Marketplace Schema

**Required fields for every plugin:**
```json
{
  "name": "string (kebab-case)",
  "source": "string (relative path from repo root)",
  "description": "string (clear, concise)",
  "version": "string (semver: x.y.z)",
  "category": "string (from valid list)",
  "keywords": "array (at least 2)",
  "author": {
    "name": "string",
    "email": "string (valid email)"
  }
}
```

**Optional fields:**
```json
{
  "repository": "string (GitHub URL)",
  "homepage": "string (docs URL)",
  "license": "string (MIT, Apache-2.0, etc.)",
  "featured": "boolean (extended only)",
  "mcpTools": "number (extended only)"
}
```

## Common Issues & Fixes

### Issue: Sync fails with schema error
```bash
# Check marketplace.extended.json syntax
jq empty .claude-plugin/marketplace.extended.json

# Common errors:
# - Missing comma
# - Invalid field type
# - Duplicate plugin name
```

### Issue: marketplace.json out of sync
```bash
# Regenerate from source
npm run sync-marketplace

# If still fails, check git status
git status .claude-plugin/
```

### Issue: Plugin not appearing
```bash
# Verify entry exists
jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.extended.json

# Check source path
ls -la ./plugins/category/plugin-name
```

## Automation

I can automatically:
1. Add plugin entries with all required fields
2. Update version across plugin + catalog
3. Sync marketplace.json
4. Validate catalog integrity
5. Check for duplicates
6. Fix common issues

## Output Format

```
📦 MARKETPLACE UPDATE REPORT

Action: Add plugin "new-plugin"
Location: plugins/productivity/new-plugin/

✅ COMPLETED STEPS:
1. Added entry to marketplace.extended.json
2. Ran npm run sync-marketplace
3. Validated marketplace.json
4. Checked for duplicates: NONE
5. Verified source path exists

📊 MARKETPLACE STATS:
Total plugins: 227 (+1)
Categories: 14
Featured: 3
Latest sync: 2025-10-16 14:30 UTC

✨ Ready to commit:
git add .claude-plugin/marketplace.extended.json .claude-plugin/marketplace.json
git commit -m "feat: Add new-plugin to marketplace"
```

## Repository-Specific Features

**For claude-code-plugins repo:**
- Manages `claude-code-plugins-plus` marketplace
- Handles both extended and CLI catalogs
- Validates against repository structure
- Checks plugin count accuracy
- Ensures featured plugins are quality plugins

## Examples

**User says:** "Add the new security-scanner plugin to marketplace"

**I automatically:**
1. Read plugin.json for metadata
2. Add entry to marketplace.extended.json
3. Run npm run sync-marketplace
4. Validate both catalogs
5. Check no duplicates
6. Report success

**User says:** "Sync the marketplace catalog"

**I automatically:**
1. Run npm run sync-marketplace
2. Validate marketplace.json generated
3. Check git diff
4. Report changes

**User says:** "Update plugin version in marketplace"

**I automatically:**
1. Find plugin entry
2. Update version in marketplace.extended.json
3. Sync marketplace.json
4. Validate versions match
5. Report success
