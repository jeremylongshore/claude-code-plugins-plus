# Maintaining The Index

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
