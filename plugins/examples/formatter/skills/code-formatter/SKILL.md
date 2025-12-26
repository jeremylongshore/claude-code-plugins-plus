---
name: code-formatter
description: |
  Automatically formats and validates code files using Prettier and other formatting tools.
  Use when users mention "format my code", "fix formatting", "apply code style",
  "check formatting", "make code consistent", or "clean up code formatting".
  Handles JavaScript, TypeScript, JSON, CSS, Markdown, and many other file types. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Code Formatter Skill

This skill provides comprehensive code formatting and validation capabilities using industry-standard tools like Prettier.



## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
## Prerequisites

- Node.js and npm/npx installed
- Prettier available globally or locally
- Write permissions for target files
- Supported file types in the project

## Instructions

### 1. Analyze Current Formatting

First, check the current formatting state of files:

```bash
# Check if prettier is available
npx prettier --version || npm install -g prettier

# Find all formattable files
find . -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.json" -o -name "*.css" -o -name "*.md" \) -not -path "*/node_modules/*" -not -path "*/dist/*"

# Check which files need formatting
npx prettier --check "**/*.{js,jsx,ts,tsx,json,css,md}" --ignore-path .prettierignore
```

### 2. Configure Formatting Rules

Create or check for existing Prettier configuration:

```javascript
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### 3. Apply Formatting

Format individual files or entire directories:

```bash
# Format a single file
npx prettier --write src/app.js

# Format all JavaScript files
npx prettier --write "**/*.js"

# Format with specific config
npx prettier --write --config .prettierrc "src/**/*.{js,jsx,ts,tsx}"

# Dry run to see what would change
npx prettier --check src/
```

### 4. Set Up Ignore Patterns

Create .prettierignore for files to skip:

```
# Dependencies
node_modules/
vendor/

# Build outputs
dist/
build/
*.min.js
*.min.css

# Generated files
coverage/
*.lock
```

### 5. Integrate with Git Hooks (Optional)

Set up pre-commit formatting:

```bash
# Install husky and lint-staged
npm install --save-dev husky lint-staged

# Configure in package.json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx,json,css,md}": [
      "prettier --write"
    ]
  }
}
```

## Output

The formatter provides detailed feedback:

### Success Output
```
✓ Formatted: src/app.js
✓ Formatted: src/components/Button.jsx
✓ Formatted: package.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Successfully formatted 3 files
```

### Validation Output
```
Checking formatting...
[warn] src/app.js
[warn] src/utils/helper.ts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Found 2 files that need formatting
```

### Error Output
```
✗ Error: Cannot format src/broken.js
  SyntaxError: Unexpected token (line 15:8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Failed to format 1 file
```

## Error Handling

Common issues and solutions:

### 1. Prettier Not Found
```bash
# Install globally
npm install -g prettier

# Or use npx (no installation needed)
npx prettier --version
```

### 2. Syntax Errors
```bash
# Validate JavaScript syntax first
npx eslint src/app.js --fix-dry-run

# Check for parsing errors
npx prettier --debug-check src/app.js
```

### 3. Configuration Conflicts
```bash
# Find all config files
find . -name ".prettier*" -o -name "prettier.config.js"

# Use specific config
npx prettier --config ./custom-prettier.json --write src/
```

### 4. Permission Issues
```bash
# Check file permissions
ls -la src/app.js

# Fix permissions if needed
chmod u+w src/app.js
```

## Resources

### File Type Support

| Extension | Language | Notes |
|-----------|----------|-------|
| .js, .jsx | JavaScript | ES6+ supported |
| .ts, .tsx | TypeScript | Type annotations preserved |
| .json | JSON | Sorts keys optionally |
| .css, .scss | CSS/SASS | Vendor prefixes handled |
| .md, .mdx | Markdown | Table formatting |
| .yaml, .yml | YAML | Preserves comments |
| .html | HTML | Attribute formatting |
| .vue | Vue | Template + script + style |
| .svelte | Svelte | Full component support |

### Configuration Options

```javascript
{
  // Semicolons
  "semi": true,              // Add semicolons

  // Quotes
  "singleQuote": true,       // Use single quotes
  "jsxSingleQuote": false,   // JSX double quotes

  // Indentation
  "tabWidth": 2,             // Spaces per tab
  "useTabs": false,          // Use spaces

  // Line Length
  "printWidth": 100,         // Line wrap length
  "proseWrap": "preserve",   // Markdown wrapping

  // Trailing Commas
  "trailingComma": "es5",    // Valid in ES5

  // Brackets
  "bracketSpacing": true,    // { foo: bar }
  "bracketSameLine": false,  // JSX brackets

  // Arrow Functions
  "arrowParens": "avoid",    // x => x vs (x) => x

  // Formatting
  "htmlWhitespaceSensitivity": "css",
  "endOfLine": "lf",
  "embeddedLanguageFormatting": "auto"
}
```

### Command Reference

```bash
# Basic formatting
prettier --write <file>           # Format file
prettier --check <file>           # Check if formatted
prettier --debug-check <file>     # Debug parse errors

# Multiple files
prettier --write "src/**/*.js"    # Glob pattern
prettier --write . --ignore-path .gitignore

# Configuration
prettier --config <path>          # Use specific config
prettier --no-config              # Ignore config files
prettier --find-config-path <file> # Show config used

# Output options
prettier --list-different         # List unformatted files
prettier --log-level debug        # Verbose output
prettier --no-color              # Disable colors

# Special options
prettier --require-pragma         # Only format with @format
prettier --insert-pragma          # Add @format comment
prettier --range-start 10 --range-end 50  # Partial format
```

### Integration Examples

**VS Code Integration:**
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**CI/CD Pipeline:**
```yaml
# GitHub Actions
- name: Check formatting
  run: npx prettier --check .

# Fail on unformatted code
- name: Enforce formatting
  run: |
    npx prettier --check . || {
      echo "Code is not formatted!"
      exit 1
    }
```

**Pre-commit Hook:**
```bash
#!/bin/sh
# .git/hooks/pre-commit

files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(js|jsx|ts|tsx|json|css|md)$')

if [ -n "$files" ]; then
  npx prettier --write $files
  git add $files
fi
```

### Performance Tips

1. **Use .prettierignore** to skip large/generated files
2. **Cache node_modules** in CI environments
3. **Run in parallel** for multiple files:
   ```bash
   find . -name "*.js" | xargs -P 4 -I {} npx prettier --write {}
   ```
4. **Use --cache** flag for incremental formatting:
   ```bash
   npx prettier --write --cache src/
   ```

### Related Tools

- **ESLint** - Linting and code quality
- **Stylelint** - CSS/SCSS linting
- **Markdownlint** - Markdown style checking
- **Black** - Python formatting
- **rustfmt** - Rust formatting
- **gofmt** - Go formatting

---

**Version**: 1.0.0
**Last Updated**: 2025-12-12
**Compatibility**: Claude Code v1.5.0+