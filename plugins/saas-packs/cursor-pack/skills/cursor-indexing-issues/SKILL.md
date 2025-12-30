---
name: cursor-indexing-issues
description: |
  Troubleshoot Cursor codebase indexing problems. Triggers on "cursor indexing",
  "cursor index", "cursor codebase", "@codebase not working", "cursor search broken".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Codebase Indexing Troubleshooting

## Understanding Indexing

### What Gets Indexed
```
Indexed:
- Source code files (.py, .js, .ts, .go, etc.)
- Configuration files
- Documentation (.md, .txt)
- Package manifests (package.json, requirements.txt)

Not indexed by default:
- Binary files
- node_modules/
- .git/
- Build outputs (dist/, build/)
- Large data files
```

### Indexing Status
```
Check status bar (bottom right):
- "Indexing..." - In progress
- "Indexed" - Complete
- "Index outdated" - Needs refresh
- No indicator - Not configured
```

## Common Indexing Issues

### Issue: Indexing Never Completes

```
Symptoms:
- Progress stuck at percentage
- Status shows "Indexing..." for hours

Solutions:
1. Check for large files/folders:
   du -sh */ | sort -h

2. Create/update .cursorignore:
   node_modules/
   .git/
   dist/
   build/
   *.log
   *.lock

3. Cancel and restart:
   Cmd+Shift+P > "Cursor: Cancel Indexing"
   Cmd+Shift+P > "Cursor: Reindex Codebase"

4. Clear index cache:
   rm -rf ~/.cursor/index/
```

### Issue: @codebase Returns Nothing

```
Symptoms:
- @codebase searches return "No results"
- AI doesn't know about your code

Debug steps:
1. Verify indexing completed (status bar)
2. Check file is not in .cursorignore
3. Verify file extension is supported
4. Try specific @filename instead
5. Reindex codebase
```

### Issue: Indexing Uses Too Much CPU/Memory

```
Symptoms:
- System slows during indexing
- High resource usage

Solutions:
1. Index during off-hours
2. Exclude large directories:
   # .cursorignore
   data/
   logs/
   tmp/

3. Limit concurrent indexing:
   Settings > Cursor > Index > Max Workers

4. Index incrementally (smaller batches)
```

### Issue: Index Outdated After Changes

```
Symptoms:
- New files not searchable
- Changes not reflected

Solutions:
1. Auto-refresh should handle this
2. Manual refresh:
   Cmd+Shift+P > "Cursor: Refresh Index"
3. Check file watcher:
   Settings > Files > Watcher Exclude
```

## .cursorignore Configuration

### Basic Setup
```gitignore
# .cursorignore (at project root)

# Dependencies
node_modules/
vendor/
.venv/
__pycache__/

# Build outputs
dist/
build/
out/
.next/
.nuxt/

# Version control
.git/

# Large files
*.log
*.csv
*.sql
*.sqlite
*.db

# Data directories
data/
datasets/
uploads/

# IDE/Editor
.idea/
.vscode/
*.swp
```

### Advanced Patterns
```gitignore
# Ignore all but include specific
*
!src/
!lib/
!*.py
!*.ts

# Size-based exclusion (manual)
# Files > 1MB should be listed explicitly
large-dataset.json
```

## Optimizing Index Performance

### For Large Codebases

```
Strategies:
1. Use workspace folders (only index active project)
2. Aggressive .cursorignore
3. Index only src/ directories
4. Disable auto-index, manual trigger only
```

### Settings for Performance

```json
// settings.json
{
  "cursor.index.enabled": true,
  "cursor.index.maxFileSize": 1048576,  // 1MB
  "cursor.index.excludePatterns": [
    "**/node_modules/**",
    "**/.git/**",
    "**/dist/**"
  ],
  "cursor.index.workers": 2  // Limit CPU usage
}
```

## Index Verification

### Testing Index Works

```
Test 1: File search
Cmd+P > type filename > should appear instantly

Test 2: @codebase query
"@codebase where is the main function defined?"

Test 3: Symbol search
Cmd+Shift+O > type function name

Test 4: Reference finding
Right-click function > "Find All References"
```

### Index Health Check

```bash
# Check index size
du -sh ~/.cursor/index/

# Check index files
ls -la ~/.cursor/index/

# Clear and rebuild if corrupted
rm -rf ~/.cursor/index/
# Then reopen project and let it reindex
```

## Monorepo Indexing

### Multi-Project Setup

```
Options:
1. Index entire monorepo (slow but complete)
2. Open specific package as workspace
3. Use .cursorignore to exclude other packages

Example .cursorignore for monorepo:
packages/*/node_modules/
packages/*/dist/
# Only index your active package
!packages/my-package/
```

### Workspace-Specific Indexing

```json
// .vscode/settings.json (per workspace)
{
  "cursor.index.rootFolders": [
    "packages/frontend",
    "packages/shared"
  ]
}
```

## Troubleshooting Checklist

```
[ ] Is indexing enabled? (Settings > Cursor > Index)
[ ] Is .cursorignore properly configured?
[ ] Are there very large files to exclude?
[ ] Is there enough disk space?
[ ] Has indexing completed? (check status bar)
[ ] Are file permissions correct?
[ ] Is the file extension supported?
[ ] Have you tried reindexing?
[ ] Are there circular symlinks?
[ ] Is antivirus interfering?
```

## Recovery Commands

```bash
# Full reset of index
rm -rf ~/.cursor/index/
rm -rf ~/.cursor/indexCache/

# Restart Cursor with fresh state
cursor --reset-user-data --disable-extensions

# Selective reindex
# Open Command Palette > "Cursor: Reindex Current File"
# Open Command Palette > "Cursor: Reindex Folder"
```
