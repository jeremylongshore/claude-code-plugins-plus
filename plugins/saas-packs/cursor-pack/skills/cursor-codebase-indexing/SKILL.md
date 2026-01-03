---
name: cursor-codebase-indexing
description: |
  Set up and optimize Cursor codebase indexing. Triggers on "cursor index setup",
  "codebase indexing", "index codebase", "cursor semantic search".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Codebase Indexing Setup

## Overview

### What is Codebase Indexing?
```
Codebase indexing creates a searchable representation of your code:
- Enables @codebase queries
- Powers semantic code search
- Improves AI context awareness
- Helps AI understand project structure
```

### Index Components
```
The index contains:
- File contents and structure
- Function/class definitions
- Import relationships
- Symbol tables
- Documentation strings
```

## Initial Setup

### Enabling Indexing
```
1. Open project in Cursor
2. Settings > Cursor > Codebase Indexing
3. Enable "Index this workspace"
4. Wait for initial indexing (status bar shows progress)
```

### First-Time Indexing
```
For new projects:
1. Open folder in Cursor
2. Indexing starts automatically
3. Monitor progress in status bar
4. "Indexed" appears when complete

Time estimates:
- Small project (<1000 files): 1-5 min
- Medium project (1000-10000 files): 5-15 min
- Large project (>10000 files): 15-60 min
```

## Configuration

### .cursorignore File
```gitignore
# .cursorignore - at project root

# Dependencies (large, not your code)
node_modules/
vendor/
.venv/
__pycache__/
*.pyc

# Build outputs (generated)
dist/
build/
out/
.next/
.nuxt/
target/

# Version control
.git/

# Large data files
*.csv
*.json  # Be selective - config jsons may be useful
*.sql
*.sqlite
*.db

# Logs
*.log
logs/

# Assets (binary)
*.png
*.jpg
*.gif
*.ico
*.woff
*.ttf

# IDE/Editor
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Test fixtures (if large)
test/fixtures/
__fixtures__/
```

### Selective Indexing
```gitignore
# Index only specific directories
*
!src/
!lib/
!app/

# Include configs
!*.config.js
!*.config.ts
!package.json
!tsconfig.json
```

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

## Using the Index

### @codebase Queries
```
Find definitions:
"@codebase where is the User class defined?"
"@codebase find all authentication-related functions"

Understand architecture:
"@codebase how is the database connection handled?"
"@codebase what are the main API routes?"

Find usage:
"@codebase where is handleLogin called?"
"@codebase show examples of using the cache"
```

### Effective Search Patterns
```
Specific:
"@codebase find the validateEmail function"
"@codebase show ProductService class methods"

Semantic:
"@codebase how do we handle authentication?"
"@codebase what's the error handling pattern?"

Exploratory:
"@codebase summarize the main modules"
"@codebase list all API endpoints"
```

## Maintaining the Index

### Manual Operations
```
Reindex entire codebase:
Cmd+Shift+P > "Cursor: Reindex Codebase"

Refresh index (incremental):
Cmd+Shift+P > "Cursor: Refresh Index"

Clear index:
Cmd+Shift+P > "Cursor: Clear Index"
```

### Auto-Update Triggers
```
Index updates automatically when:
- Files are saved
- Files are created/deleted
- Git operations complete
- Workspace is opened
```

### Index Health Check
```bash
# Check index status
Cursor status bar shows:
- "Indexing..." - In progress
- "Indexed" - Complete
- "Index Error" - Problem

# Check index size
ls -la ~/.cursor/index/

# Verify index works
@codebase find main function
```

## Optimization for Large Projects

### Monorepo Strategy
```
Option 1: Open specific package
cd monorepo/packages/my-package
cursor .

Option 2: Selective .cursorignore
# .cursorignore
packages/*/node_modules/
packages/*/dist/
# Only index active packages
!packages/frontend/
!packages/shared/
```

### Performance Tuning
```json
{
  // Reduce workers for slower machines
  "cursor.index.workers": 2,

  // Increase for faster machines
  "cursor.index.workers": 8,

  // Limit concurrent file processing
  "cursor.index.maxConcurrentFiles": 50
}
```

### Incremental Indexing
```
For very large codebases:
1. Start with essential directories only
2. Add more as needed
3. Use .cursorignore aggressively
4. Consider workspace subsets
```

## Troubleshooting

### Index Not Updating
```
Symptoms: Changes not reflected in @codebase

Fixes:
1. Wait for save to trigger update
2. Manual refresh: "Cursor: Refresh Index"
3. Check file isn't in .cursorignore
4. Verify file type is supported
```

### Search Returns Nothing
```
Symptoms: @codebase queries return empty

Fixes:
1. Verify indexing completed
2. Check file isn't excluded
3. Try simpler query
4. Reindex if corrupt
```

### High Resource Usage
```
Symptoms: CPU/memory spike during indexing

Fixes:
1. Reduce worker count
2. Add more exclusions
3. Index during off-hours
4. Use smaller workspace
```

## Best Practices

### Project Setup
```
1. Create .cursorignore before opening
2. Configure settings before first index
3. Wait for complete index before using
4. Test @codebase with known function
```

### Ongoing Maintenance
```
Weekly:
- Check index health
- Review .cursorignore

After major changes:
- Force reindex
- Verify new files indexed

When issues occur:
- Clear and rebuild index
- Check exclusion patterns
```
