---
name: format
description: Format code files using Prettier
---

# Format Command

Format code files using Prettier with automatic detection of file types and configuration.

## Usage

To format files in your project, I'll:

1. **Check Prerequisites** - Verify Prettier is installed
2. **Detect Configuration** - Find existing .prettierrc or use defaults
3. **Analyze Files** - Identify which files need formatting
4. **Apply Formatting** - Format selected files with Prettier
5. **Report Results** - Show what was changed

## Supported File Types

- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- JSON (.json)
- CSS/SCSS (.css, .scss, .less)
- Markdown (.md, .mdx)
- HTML (.html)
- YAML (.yaml, .yml)
- Vue (.vue)
- Svelte (.svelte)

## Examples

Common usage patterns:

```bash
# Format all JavaScript files
/format **/*.js

# Format specific file
/format src/app.js

# Format entire directory
/format src/

# Check formatting without changes
/format --check

# Format with specific config
/format --config custom-prettier.json src/
```

## Options

- `--check` - Only check if files are formatted, don't modify
- `--config <path>` - Use specific Prettier configuration
- `--ignore-path <path>` - Use specific ignore file
- `--write` - Write changes to files (default)

## Configuration

The command looks for configuration in this order:

1. `.prettierrc` or `.prettierrc.json`
2. `prettier.config.js`
3. `package.json` prettier field
4. Default configuration (if none found)

## Output

The command provides detailed feedback:

```
✓ Formatted: src/app.js
✓ Formatted: src/components/Button.jsx
✗ Error: src/broken.js (syntax error)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Successfully formatted 2/3 files
```

## Note

This command requires Node.js and Prettier to be installed in your environment.