# System Resource Management

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
