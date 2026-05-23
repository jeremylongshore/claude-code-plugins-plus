# Indexing Errors

## Indexing Errors

### "Indexing Failed"

```
Symptoms: @codebase doesn't work, search fails

Solutions:
1. Check disk space
2. Exclude large folders (.git, node_modules)
3. Restart indexing: Cmd+Shift+P > "Reindex"
4. Check file permissions
5. Reduce codebase size if too large

Exclusions (.cursorignore):
node_modules/
.git/
dist/
build/
*.lock
```

### "Indexing Stuck"

```
Symptoms: Progress bar frozen, never completes

Solutions:
1. Cancel and restart indexing
2. Clear index cache
3. Check for circular symlinks
4. Exclude problematic directories
5. Restart Cursor
```
