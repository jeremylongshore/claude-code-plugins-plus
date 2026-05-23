# Examples

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
