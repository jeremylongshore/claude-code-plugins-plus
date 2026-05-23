# Index Settings

## Index Settings

### Performance Settings

```json
// settings.json
{
  // Maximum file size to index (bytes)
  "cursor.index.maxFileSize": 1048576,  // 1MB

  // Number of indexing workers
  "cursor.index.workers": 4,

  // Index on save
  "cursor.index.indexOnSave": true,

  // Background indexing
  "cursor.index.backgroundIndexing": true
}
```

### Language-Specific Settings

```json
{
  // Include/exclude by language
  "cursor.index.includeLanguages": [
    "typescript",
    "javascript",
    "python",
    "go",
    "rust"
  ],

  // Exclude specific patterns
  "cursor.index.excludePatterns": [
    "**/*.min.js",
    "**/*.generated.ts",
    "**/migrations/*.sql"
  ]
}
```
