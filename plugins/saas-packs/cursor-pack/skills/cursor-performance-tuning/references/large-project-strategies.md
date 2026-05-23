# Large Project Strategies

## Large Project Strategies

### Monorepo Performance

```json
{
  // Only watch active package
  "files.watcherExclude": {
    "**/packages/!(my-package)/**": true
  },

  // Limit search
  "search.exclude": {
    "**/packages/!(my-package)/**": true
  }
}
```

### Workspace Folders

```
Instead of opening entire monorepo:

Option 1: Open specific package
cursor packages/my-package

Option 2: Use workspace file
{
  "folders": [
    { "path": "packages/my-package" }
  ]
}
```

### Remote Development

```
For very large projects:
1. Use Remote-SSH extension
2. Run Cursor UI locally
3. Code lives on remote server
4. Better network latency for AI
```
