# Version Bump Process

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
