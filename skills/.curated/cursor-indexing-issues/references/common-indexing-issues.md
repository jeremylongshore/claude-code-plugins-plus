# Common Indexing Issues

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
