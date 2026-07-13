## Error Handling Reference

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
