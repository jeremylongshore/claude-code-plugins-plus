# Indexing Strategy

## Indexing Strategy

### Selective Indexing

```gitignore
# .cursorignore for multi-repo

# Index only your active work
*

# Include what you're working on
!apps/web/
!packages/shared/
!packages/ui/

# Still exclude heavy stuff
apps/web/node_modules/
apps/web/.next/
```

### Per-Project Indexing

```json
// workspace settings
{
  "cursor.index.excludePatterns": [
    "**/node_modules/**",
    "**/.next/**",
    "**/dist/**",
    "apps/legacy/**"  // Don't index old app
  ]
}
```
