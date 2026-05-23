# Performance Errors

## Performance Errors

### "High CPU Usage"

```
Symptoms: Cursor uses 100% CPU, system slow

Solutions:
1. Disable unused extensions
2. Close unused tabs
3. Exclude large folders from watch
4. Reduce completion model complexity
5. Check for infinite loops in extensions

Settings:
{
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/**": true
  }
}
```

### "High Memory Usage"

```
Symptoms: Cursor using GB of RAM

Solutions:
1. Restart Cursor
2. Close unused workspaces
3. Limit search scope
4. Disable memory-heavy extensions
5. Reduce open files
```
