# Editor Optimization

## Editor Optimization

### Reduce Visual Overhead

```json
// settings.json
{
  // Disable expensive features
  "editor.minimap.enabled": false,
  "editor.renderWhitespace": "none",
  "editor.renderLineHighlight": "none",
  "editor.roundedSelection": false,
  "editor.scrollBeyondLastLine": false,
  "editor.smoothScrolling": false,
  "breadcrumbs.enabled": false,

  // Reduce rendering
  "editor.cursorBlinking": "solid",
  "editor.cursorSmoothCaretAnimation": "off",

  // Limit tokenization
  "editor.maxTokenizationLineLength": 5000
}
```

### File Handling

```json
{
  // Limit open editors
  "workbench.editor.limit.enabled": true,
  "workbench.editor.limit.value": 10,

  // Disable auto-save (optional)
  "files.autoSave": "off",

  // Exclude files from watching
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/dist/**": true,
    "**/build/**": true,
    "**/.next/**": true
  }
}
```

### Search Optimization

```json
{
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/coverage": true,
    "**/.git": true,
    "**/*.lock": true
  },
  "search.followSymlinks": false,
  "search.useIgnoreFiles": true
}
```
