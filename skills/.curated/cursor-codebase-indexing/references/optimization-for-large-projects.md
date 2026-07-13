# Optimization For Large Projects

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
