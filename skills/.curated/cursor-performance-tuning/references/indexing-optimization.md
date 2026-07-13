# Indexing Optimization

## Indexing Optimization

### Aggressive Exclusions

```gitignore
# .cursorignore

# Large dependencies
node_modules/
vendor/
.venv/

# Build outputs
dist/
build/
.next/
out/

# Large files
*.log
*.csv
*.json
*.sql
*.sqlite

# Generated code
*.generated.*
*.min.js
*.bundle.js

# Test fixtures
__fixtures__/
test/fixtures/
```

### Indexing Settings

```json
{
  // Limit indexing scope
  "cursor.index.maxFileSize": 500000,  // 500KB
  "cursor.index.workers": 2,  // Reduce CPU usage
  "cursor.index.backgroundIndexing": false  // Manual only
}
```
