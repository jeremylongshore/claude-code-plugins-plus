---
name: format-check
description: Check if files are properly formatted without making changes
---

# Format Check Command

Validate code formatting without making any changes. Perfect for CI/CD pipelines and pre-commit checks.

## Usage

I'll check your code formatting by:

1. **Scanning Files** - Find all formattable files
2. **Validating Format** - Check against Prettier rules
3. **Reporting Issues** - List files that need formatting
4. **Exit Status** - Return success/failure for CI integration

## Examples

```bash
# Check all files
/format-check

# Check specific directory
/format-check src/

# Check specific file types
/format-check **/*.js

# Check with custom config
/format-check --config .prettierrc.strict src/
```

## Output Examples

### All Files Formatted
```
Checking formatting...
✓ src/app.js
✓ src/components/Button.jsx
✓ package.json
━━━━━━━━━━━━━━━━━━━━━━━
✅ All 3 files are properly formatted
```

### Files Need Formatting
```
Checking formatting...
✓ src/app.js
⚠ src/components/Button.jsx
⚠ package.json
━━━━━━━━━━━━━━━━━━━━━━━
⚠ Found 2 files that need formatting

Files requiring formatting:
- src/components/Button.jsx
- package.json

Run /format to fix these issues
```

## CI/CD Integration

Use in GitHub Actions:

```yaml
- name: Check code formatting
  run: |
    /plugin install formatter@claude-code-plugins-plus
    /format-check || exit 1
```

## Note

This command only checks formatting, it never modifies files. Use `/format` to actually apply formatting.