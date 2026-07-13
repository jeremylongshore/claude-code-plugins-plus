# Troubleshooting

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
