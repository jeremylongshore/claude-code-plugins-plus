---
name: version-bumper
description: |
  Automatically handles semantic version updates across plugin.json and marketplace catalog when user mentions version bump, update version, or release. Ensures version consistency in claude-code-plugins repository.
allowed-tools: Read, Write, Edit, Grep, Bash
version: 1.0.0
---

# Version Bumper

## Purpose
Automatically manages semantic version updates for Claude Code plugins, ensuring consistency across plugin.json, marketplace catalog, and git tags - optimized for claude-code-plugins repository workflow.

## Trigger Keywords
- "bump version" or "update version"
- "release" or "new release"
- "major version" or "minor version" or "patch version"
- "increment version"
- "version update"

## Semantic Versioning

**Format:** MAJOR.MINOR.PATCH (e.g., 2.1.3)

**Rules:**
- **MAJOR (2.x.x)** - Breaking changes, incompatible API changes
- **MINOR (x.1.x)** - New features, backward compatible
- **PATCH (x.x.3)** - Bug fixes, backward compatible

**Examples:**
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.0` → `1.1.0` (new feature)
- `1.0.0` → `2.0.0` (breaking change)

## Version Bump Process

When activated, I will:

1. **Identify Current Version**
   ```bash
   # Read plugin version
   current=$(jq -r '.version' .claude-plugin/plugin.json)
   echo "Current version: $current"
   ```

2. **Determine Bump Type**
   - From user request (major/minor/patch)
   - Or suggest based on changes
   - Or ask user which type

3. **Calculate New Version**
   ```bash
   # Example for patch bump: 1.2.3 → 1.2.4
   IFS='.' read -r major minor patch <<< "$current"
   new_version="$major.$minor.$((patch + 1))"
   ```

4. **Update Files**
   - Update `.claude-plugin/plugin.json`
   - Update `.claude-plugin/marketplace.extended.json`
   - Sync to `marketplace.json`

5. **Validate Consistency**
   - Verify all files have same version
   - Check no other plugins use this version
   - Validate semver format

6. **Create Git Tag (Optional)**
   ```bash
   git tag -a "v$new_version" -m "Release v$new_version"
   ```

## Update Locations

### 1. Plugin JSON
```json
// .claude-plugin/plugin.json
{
  "name": "plugin-name",
  "version": "1.2.4",  // ← Update here
  ...
}
```

### 2. Marketplace Extended
```json
// .claude-plugin/marketplace.extended.json
{
  "plugins": [
    {
      "name": "plugin-name",
      "version": "1.2.4",  // ← Update here
      ...
    }
  ]
}
```

### 3. Sync CLI Catalog
```bash
npm run sync-marketplace
# Regenerates marketplace.json with new version
```

## Bump Types

### Patch Bump (Bug Fix)
**When to use:**
- Bug fixes
- Documentation updates
- Minor improvements
- No new features

**Example:** 1.2.3 → 1.2.4

### Minor Bump (New Feature)
**When to use:**
- New features
- New commands/agents/skills
- Backward compatible changes
- Enhanced functionality

**Example:** 1.2.3 → 1.3.0

### Major Bump (Breaking Change)
**When to use:**
- Breaking API changes
- Incompatible updates
- Major refactor
- Removed features

**Example:** 1.2.3 → 2.0.0

## Validation Checks

Before bumping:
- ✅ Current version is valid semver
- ✅ New version is higher than current
- ✅ No other plugin uses new version
- ✅ All files have same current version
- ✅ Git working directory is clean (optional)

After bumping:
- ✅ plugin.json updated
- ✅ marketplace.extended.json updated
- ✅ marketplace.json synced
- ✅ All versions consistent
- ✅ CHANGELOG.md updated (if exists)

## Changelog Management

If CHANGELOG.md exists, I update it:

```markdown
# Changelog

## [1.2.4] - 2025-10-16

### Fixed
- Bug fix description
- Another fix

## [1.2.3] - 2025-10-15
...
```

## Git Integration

### Option 1: Version Commit
```bash
# Update version files
git add .claude-plugin/plugin.json
git add .claude-plugin/marketplace.extended.json
git add .claude-plugin/marketplace.json
git add CHANGELOG.md  # if exists

# Commit version bump
git commit -m "chore: Bump plugin-name to v1.2.4"
```

### Option 2: Version Tag
```bash
# Create annotated tag
git tag -a "plugin-name-v1.2.4" -m "Release plugin-name v1.2.4"

# Or for monorepo
git tag -a "v1.2.4" -m "Release v1.2.4"

# Push tag
git push origin plugin-name-v1.2.4
```

## Multi-Plugin Updates

For repository-wide version bump:

```bash
# Bump marketplace version
jq '.metadata.version = "1.0.40"' .claude-plugin/marketplace.extended.json

# Update all plugins (if needed)
for plugin in plugins/*/; do
  # Update plugin.json
  # Update marketplace entry
done
```

## Version Consistency Check

I verify:
```bash
# Plugin version
plugin_v=$(jq -r '.version' plugins/category/plugin-name/.claude-plugin/plugin.json)

# Marketplace version
market_v=$(jq -r '.plugins[] | select(.name == "plugin-name") | .version' .claude-plugin/marketplace.extended.json)

# Should match
if [ "$plugin_v" != "$market_v" ]; then
  echo "❌ Version mismatch!"
  echo "Plugin: $plugin_v"
  echo "Marketplace: $market_v"
fi
```

## Release Workflow

Complete release process:

1. **Determine Bump Type**
   - Review changes since last version
   - Decide: patch/minor/major

2. **Update Version**
   - Bump plugin.json
   - Update marketplace catalog
   - Sync marketplace.json

3. **Update Changelog**
   - Add release notes
   - List changes
   - Include date

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "chore: Release v1.2.4"
   ```

5. **Create Tag**
   ```bash
   git tag -a "v1.2.4" -m "Release v1.2.4"
   ```

6. **Push**
   ```bash
   git push origin main
   git push origin v1.2.4
   ```

7. **Validate**
   - Check GitHub release created
   - Verify marketplace updated
   - Test plugin installation

## Output Format

```
🔢 VERSION BUMP REPORT

Plugin: plugin-name
Old Version: 1.2.3
New Version: 1.2.4
Bump Type: PATCH

✅ UPDATES COMPLETED:
1. Updated .claude-plugin/plugin.json → v1.2.4
2. Updated marketplace.extended.json → v1.2.4
3. Synced marketplace.json → v1.2.4
4. Updated CHANGELOG.md

📊 CONSISTENCY CHECK:
✅ All files have version 1.2.4
✅ No version conflicts
✅ Semantic versioning valid

📝 CHANGELOG ENTRY:
## [1.2.4] - 2025-10-16
### Fixed
- Bug fix description

🎯 NEXT STEPS:
1. Review changes: git diff
2. Commit: git add . && git commit -m "chore: Bump to v1.2.4"
3. Tag: git tag -a "v1.2.4" -m "Release v1.2.4"
4. Push: git push origin main && git push origin v1.2.4

✨ Ready to release!
```

## Repository-Specific Features

**For claude-code-plugins repo:**
- Handles both plugin and marketplace versions
- Updates marketplace metadata version
- Manages plugin count in README
- Syncs both catalog files
- Creates proper release tags

## Examples

**User says:** "Bump the security-scanner plugin to patch version"

**I automatically:**
1. Read current version: 1.2.3
2. Calculate patch bump: 1.2.4
3. Update plugin.json
4. Update marketplace.extended.json
5. Sync marketplace.json
6. Validate consistency
7. Report success

**User says:** "Release version 2.0.0 of plugin-name"

**I automatically:**
1. Recognize major version (breaking change)
2. Update all version files
3. Update CHANGELOG.md with major release notes
4. Create git commit
5. Create git tag v2.0.0
6. Provide push commands

**User says:** "Increment version for new feature"

**I automatically:**
1. Detect this is a minor bump
2. Calculate new version (1.2.3 → 1.3.0)
3. Update all files
4. Add changelog entry
5. Report completion
