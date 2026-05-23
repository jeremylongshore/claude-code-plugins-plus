## Implementation Guide

1. Analyze current formatting (`prettier --check`) and identify files to update.
2. Configure formatting rules (`.prettierrc`, `.editorconfig`) for the project.
3. Apply formatting (`prettier --write`) to the target files/directories.
4. Add ignore patterns (`.prettierignore`) for generated/vendor outputs.
5. Optionally enforce formatting via git hooks (husky/lint-staged).

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
