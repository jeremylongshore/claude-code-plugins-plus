# Validation Report Format

## Validation Report Format

```
🔍 PLUGIN VALIDATION REPORT
Plugin: plugin-name
Location: plugins/category/plugin-name/

✅ PASSED CHECKS (8/10)
- Required files present
- Valid plugin.json schema
- Proper frontmatter format
- Directory structure correct
- No security issues
- Marketplace compliance
- README complete
- JSON valid

❌ FAILED CHECKS (2/10)
- Script permissions: 3 .sh files not executable
  Fix: chmod +x scripts/*.sh

- Marketplace version mismatch
  plugin.json: v1.2.0
  marketplace.extended.json: v1.1.0
  Fix: Update marketplace.extended.json to v1.2.0

⚠️  WARNINGS (1)
- README missing usage examples
  Recommendation: Add ## Usage section with examples

OVERALL: FAILED (2 critical issues)
Fix issues above before committing.
```
