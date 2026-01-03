---
name: cursor-performance-tuning
description: |
  Optimize Cursor IDE performance. Triggers on "cursor performance",
  "cursor slow", "cursor optimization", "cursor memory", "speed up cursor".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Performance Tuning

## Performance Diagnostics

### Checking Performance
```
1. Process Explorer
   Help > Process Explorer
   - View CPU/memory per process
   - Identify heavy extensions
   - Monitor extension hosts

2. Developer Tools
   Help > Toggle Developer Tools
   - Performance tab
   - Memory profiling
   - Network requests

3. Startup Performance
   Cmd+Shift+P > "Startup Performance"
   - Extension load times
   - Activation events
```

### Common Performance Issues
```
Symptoms → Likely Cause:

Slow startup → Many extensions, large workspace
Laggy typing → Heavy extensions, large files
High CPU → Runaway extension, indexing
High memory → Many open files, large project
Slow completions → Network latency, model choice
```

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

## Extension Optimization

### Audit Extensions
```
1. List all extensions:
   cursor --list-extensions

2. Check which are active:
   Help > Process Explorer > Extension Host

3. Disable unused:
   Extensions panel > Right-click > Disable

4. Remove unnecessary:
   cursor --uninstall-extension [id]
```

### Workspace-Specific Extensions
```json
// Only enable project-relevant extensions
// .vscode/settings.json
{
  "extensions.autoUpdate": "onlyEnabledExtensions"
}

// Disable globally, enable per-workspace
// For heavy extensions like language servers
```

### Extension Load Optimization
```json
{
  // Delay extension activation
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,

  // Disable telemetry (slight improvement)
  "telemetry.telemetryLevel": "off"
}
```

## AI Feature Optimization

### Completion Speed
```json
{
  // Use faster model for completions
  "cursor.completion.model": "gpt-3.5-turbo",

  // Adjust delay
  "cursor.completion.delay": 200,

  // Limit completion length
  "cursor.completion.maxLength": 500
}
```

### Context Management
```
Reduce context for faster responses:
1. Select less code
2. Fewer @-mentions
3. Shorter conversations
4. Clear chat history

Use .cursorignore aggressively:
- Exclude non-essential files
- Focus on active development areas
```

### Model Selection
```
Speed vs Quality:

Fastest: cursor-small, gpt-3.5-turbo
Balanced: gpt-4-turbo
Thorough: gpt-4, claude-3-opus

Use faster models for:
- Simple completions
- Quick lookups
- Repetitive tasks
```

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

## System Resource Management

### Memory Optimization
```bash
# Monitor Cursor memory
# macOS
top -pid $(pgrep -f Cursor)

# Linux
ps aux | grep Cursor

# If high memory:
1. Close unused tabs
2. Restart Cursor
3. Clear extension data
```

### CPU Optimization
```
Reduce CPU usage:

1. Disable file watchers for large folders
2. Reduce extension count
3. Lower indexing workers
4. Disable live error checking
5. Manual save instead of auto-save
```

### Disk I/O
```
Improve disk performance:

1. Use SSD for workspace
2. Exclude from antivirus scanning:
   - ~/.cursor/
   - Workspace folder
3. Clear Cursor cache periodically:
   rm -rf ~/Library/Caches/Cursor/
```

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

## Performance Checklist

### Daily
```
[ ] Close unused tabs
[ ] Clear terminal output
[ ] Check for hanging processes
```

### Weekly
```
[ ] Review extension list
[ ] Clear cache if slow
[ ] Check disk space
[ ] Update Cursor and extensions
```

### Monthly
```
[ ] Audit extensions (disable unused)
[ ] Review .cursorignore
[ ] Clean up workspace
[ ] Profile performance
```

## Troubleshooting

### Cursor Won't Start
```bash
# Start without extensions
cursor --disable-extensions

# Reset user data
rm -rf ~/Library/Application\ Support/Cursor/

# Clear GPU cache
cursor --disable-gpu
```

### Extreme Slowness
```
1. Disable all extensions
2. Open empty folder
3. If fast: extension or project issue
4. If slow: reinstall Cursor
```

### Memory Leak
```
Symptoms: Memory grows over time

Solutions:
1. Restart Cursor periodically
2. Find leaking extension
3. Report to Cursor/extension devs
4. Reduce open files
```
